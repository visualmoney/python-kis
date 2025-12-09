"""
통합 테스트 - Rate Limit 준수 확인

대량 요청 시 Rate Limiting이 올바르게 작동하는지 확인합니다.
"""

import pytest
import time
from unittest.mock import Mock, patch
import requests_mock
from pykis import PyKis, KisAuth
from pykis.utils.rate_limit import RateLimiter


@pytest.fixture
def mock_auth():
    """테스트용 인증 정보"""
    return KisAuth(
        id="test_user",
        account="50000000-01",
        appkey="P" + "A" * 35,
        secretkey="S" * 180,
    )


class TestRateLimitCompliance:
    """Rate Limit 준수 확인 통합 테스트"""

    def test_rate_limit_enforced_on_api_calls(self, mock_auth):
        """API 호출 시 Rate Limit 강제"""
        with requests_mock.Mocker() as m:
            # 토큰 발급
            m.post(
                "https://openapivts.koreainvestment.com:29443/oauth2/tokenP",
                json={"access_token": "test_token"}
            )
            
            # API 응답
            m.get(
                requests_mock.ANY,
                json={"rt_cd": "0", "output": {}}
            )
            
            kis = PyKis(mock_auth, use_websocket=False)
            
            start_time = time.time()
            
            # 모의투자: 초당 1개 제한
            # 5번 요청 시 약 4초 소요되어야 함
            for i in range(5):
                kis.request(
                    f"/test/api/{i}",
                    method="GET",
                    domain="virtual"
                )
            
            elapsed = time.time() - start_time
            
            # 약 4-5초 소요 (초당 1개 제한)
            assert 3.5 <= elapsed <= 5.5

    def test_rate_limit_real_vs_virtual(self):
        """실전과 모의투자 Rate Limit 차이"""
        # 실전: 초당 19개
        real_limiter = RateLimiter(max_requests=19, per_seconds=1.0)
        
        # 모의: 초당 1개  
        virtual_limiter = RateLimiter(max_requests=1, per_seconds=1.0)
        
        # 실전은 빠름
        start = time.time()
        for _ in range(19):
            real_limiter.wait()
            real_limiter.on_success()
        real_elapsed = time.time() - start
        
        assert real_elapsed < 1.0
        
        # 모의는 느림
        start = time.time()
        for _ in range(5):
            virtual_limiter.wait()
            virtual_limiter.on_success()
        virtual_elapsed = time.time() - start
        
        assert virtual_elapsed >= 4.0

    def test_concurrent_requests_respect_limit(self, mock_auth):
        """동시 요청도 Rate Limit 준수"""
        from threading import Thread
        
        with requests_mock.Mocker() as m:
            m.post(
                "https://openapivts.koreainvestment.com:29443/oauth2/tokenP",
                json={"access_token": "test_token"}
            )
            
            m.get(
                requests_mock.ANY,
                json={"rt_cd": "0", "output": {}}
            )
            
            kis = PyKis(mock_auth, use_websocket=False)
            
            results = []
            
            def make_request(index):
                try:
                    kis.request(
                        f"/test/api/{index}",
                        method="GET",
                        domain="virtual"
                    )
                    results.append(time.time())
                except Exception as e:
                    pass
            
            start_time = time.time()
            
            # 10개 스레드에서 각 1번씩 = 총 10개
            threads = [Thread(target=make_request, args=(i,)) for i in range(10)]
            
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            
            elapsed = time.time() - start_time
            
            # 초당 1개 제한 -> 약 10초
            assert 9.0 <= elapsed <= 11.0

    def test_rate_limit_error_handling(self):
        """에러 발생 시 Rate Limit 처리"""
        limiter = RateLimiter(max_requests=5, per_seconds=1.0)
        
        # 성공 5번
        for _ in range(5):
            limiter.wait()
            limiter.on_success()
        
        # 에러 5번 (카운트 안 됨)
        for _ in range(5):
            limiter.wait()
            limiter.on_error()
        
        # 성공 5번 더 (즉시 가능해야 함, 에러는 카운트 안 됨)
        start = time.time()
        for _ in range(5):
            limiter.wait()
            limiter.on_success()
        elapsed = time.time() - start
        
        # 바로 실행되거나, 약간의 대기만
        assert elapsed < 2.0

    def test_rate_limit_burst_then_throttle(self):
        """초기 버스트 후 throttle"""
        limiter = RateLimiter(max_requests=10, per_seconds=1.0)
        
        start_time = time.time()
        request_times = []
        
        # 30개 요청
        for _ in range(30):
            limiter.wait()
            request_times.append(time.time() - start_time)
            limiter.on_success()
        
        # 처음 10개는 빠름 (<0.5초)
        assert all(t < 0.5 for t in request_times[:10])
        
        # 그 다음부터는 throttle
        # 11-20번째: 1초 ~ 2초 사이
        assert all(1.0 <= t < 2.5 for t in request_times[10:20])
        
        # 21-30번째: 2초 ~ 3초 사이
        assert all(2.0 <= t < 3.5 for t in request_times[20:30])

    def test_rate_limit_with_variable_intervals(self):
        """가변 간격으로 요청"""
        limiter = RateLimiter(max_requests=5, per_seconds=1.0)
        
        timestamps = []
        
        # 요청 사이사이 0.3초 대기
        for i in range(10):
            limiter.wait()
            timestamps.append(time.time())
            limiter.on_success()
            
            if i < 9:  # 마지막은 대기 안 함
                time.sleep(0.3)
        
        # 전체 시간 계산
        total_time = timestamps[-1] - timestamps[0]
        
        # 10개 요청, 초당 5개 = 2초 + 대기시간(0.3 * 9 = 2.7초) = 약 4.7초
        # 하지만 대기 중에 시간이 지나가므로 실제로는 더 짧을 수 있음
        assert 2.5 <= total_time <= 5.0


class TestRateLimitMonitoring:
    """Rate Limit 모니터링 테스트"""

    def test_rate_limit_count_tracking(self):
        """카운트 추적"""
        limiter = RateLimiter(max_requests=10, per_seconds=1.0)
        
        # 5번 성공
        for _ in range(5):
            limiter.wait()
            limiter.on_success()
        
        assert limiter.count == 5
        
        # 3번 에러
        for _ in range(3):
            limiter.wait()
            limiter.on_error()
        
        assert limiter.count == 5  # 에러는 카운트 안 됨

    def test_rate_limit_remaining_capacity(self):
        """남은 용량 확인"""
        limiter = RateLimiter(max_requests=10, per_seconds=1.0)
        
        # 7번 요청
        for _ in range(7):
            limiter.wait()
            limiter.on_success()
        
        assert limiter.count == 7
        
        # 3개 더 즉시 가능해야 함
        start = time.time()
        for _ in range(3):
            limiter.wait()
            limiter.on_success()
        elapsed = time.time() - start
        
        assert elapsed < 0.1  # 거의 즉시

    def test_rate_limit_callback_invocation(self):
        """콜백 호출 확인"""
        callback_calls = []
        
        def callback(remaining):
            callback_calls.append(remaining)
        
        limiter = RateLimiter(max_requests=2, per_seconds=1.0, callback=callback)
        
        # 3번 요청
        for _ in range(3):
            limiter.wait()
            limiter.on_success()
        
        # 적어도 1번은 콜백 호출되어야 함 (3번째에서)
        assert len(callback_calls) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
