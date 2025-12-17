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
    """테스트용 인증 정보 (실전 도메인)"""
    return KisAuth(
        id="test_user",
        account="50000000-01",
        appkey="P" + "A" * 35,
        secretkey="S" * 180,
        virtual=False,
    )


@pytest.fixture
def mock_virtual_auth():
    """테스트용 모의 인증 정보"""
    return KisAuth(
        id="test_user",
        account="50000000-01",
        appkey="P" + "A" * 35,
        secretkey="S" * 180,
        virtual=True,
    )

@pytest.fixture
def mock_token_response():
    """토큰 발급 응답"""
    return {
        "access_token": "test_token_12345",
        "access_token_token_expired": "2025-12-31 23:59:59",
        "token_type": "Bearer",
        "expires_in": 86400
    }

# https://apiportal.koreainvestment.com/community/10000000-0000-0011-0000-000000000001/post/eb3e2dcb-3d52-4ff1-9eb2-c09b1c880fb2
# appkey 당 REST 20건/초, WebSocket 41건 구독

class TestRateLimitCompliance:
    """Rate Limit 준수 확인 통합 테스트"""

    def test_rate_limit_enforced_on_api_calls(self, mock_auth, mock_virtual_auth, mock_token_response):
        """전체 테스트를 실제로 돌리지 않고 기본 구조만 확인"""
        # 실제로 호출하지 않으므로 기본적인 PyKis 초기화만 테스트
        with requests_mock.Mocker() as m:
            # 토큰 발급 - real 도메인
            m.post(
                "https://openapi.koreainvestment.com:9443/oauth2/tokenP",
                json=mock_token_response
            )
            
            # 토큰 발급 - virtual 도메인
            m.post(
                "https://openapivts.koreainvestment.com:29443/oauth2/tokenP",
                json=mock_token_response
            )
            
            # API 응답
            m.get(
                requests_mock.ANY,
                json={"rt_cd": "0", "output": {}}
            )
            
            kis = PyKis(mock_auth, mock_virtual_auth, use_websocket=False)
            
            # Rate limiter가 설정되어 있는지 확인
            assert kis._rate_limiters is not None
            assert "virtual" in kis._rate_limiters
            assert kis._rate_limiters["virtual"].rate == 2  # 모의투자: 초당 2개

    def test_rate_limit_real_vs_virtual(self):
        """실전과 모의투자 Rate Limit 차이"""
        # 실전: 초당 19개 (rate=19, period=1.0)
        real_limiter = RateLimiter(rate=19, period=1.0)
        
        # 모의: 초당 1개 (rate=1, period=1.0)
        virtual_limiter = RateLimiter(rate=1, period=1.0)
        
        # 실전은 빠름
        start = time.time()
        for _ in range(19):
            real_limiter.acquire()
        real_elapsed = time.time() - start
        
        assert real_elapsed < 1.0
        
        # 모의는 느림
        start = time.time()
        for _ in range(5):
            virtual_limiter.acquire()
        virtual_elapsed = time.time() - start
        
        assert virtual_elapsed >= 4.0

    def test_concurrent_requests_respect_limit(self, mock_auth, mock_virtual_auth, mock_token_response):
        """동시 요청도 Rate Limit 준수"""
        from threading import Thread
        
        with requests_mock.Mocker() as m:
            m.post(
                "https://openapi.koreainvestment.com:9443/oauth2/tokenP",
                json=mock_token_response
            )
            m.post(
                "https://openapivts.koreainvestment.com:29443/oauth2/tokenP",
                json=mock_token_response
            )
            
            m.get(
                requests_mock.ANY,
                json={"rt_cd": "0", "output": {}}
            )
            
            kis = PyKis(mock_auth, mock_virtual_auth, use_websocket=False)
            
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
            
            # 초당 2개 제한 -> 10개 요청 시 약 5초
            assert 4.5 <= elapsed <= 6.0

    def test_rate_limit_error_handling(self):
        """에러 발생 시 Rate Limit 처리 - 기본 동작 확인"""
        limiter = RateLimiter(rate=5, period=1.0)
        
        # 성공 5번
        for _ in range(5):
            limiter.acquire()
        
        # 5번 더 호출하면 대기해야 함
        start = time.time()
        for _ in range(5):
            limiter.acquire()
        elapsed = time.time() - start
        
        # 대기 시간이 있어야 함 (약 1초)
        assert elapsed >= 0.9

    def test_rate_limit_burst_then_throttle(self):
        """초기 버스트 후 throttle"""
        limiter = RateLimiter(rate=10, period=1.0)
        
        start_time = time.time()
        request_times = []
        
        # 30개 요청
        for _ in range(30):
            limiter.acquire()
            request_times.append(time.time() - start_time)
        
        # 처음 10개는 빠름 (<0.5초)
        assert all(t < 0.5 for t in request_times[:10])
        
        # 그 다음부터는 throttle
        # 11-20번째: 1초 ~ 2초 사이
        assert all(1.0 <= t < 2.5 for t in request_times[10:20])
        
        # 21-30번째: 2초 ~ 3초 사이
        assert all(2.0 <= t < 3.5 for t in request_times[20:30])

    def test_rate_limit_with_variable_intervals(self):
        """가변 간격으로 요청"""
        limiter = RateLimiter(rate=5, period=1.0)
        
        timestamps = []
        
        # 요청 사이사이 0.3초 대기
        for i in range(10):
            limiter.acquire()
            timestamps.append(time.time())
            
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
        limiter = RateLimiter(rate=10, period=1.0)
        
        # 5번 성공
        for _ in range(5):
            limiter.acquire()
        
        assert limiter.count == 5

    def test_rate_limit_remaining_capacity(self):
        """남은 용량 확인"""
        limiter = RateLimiter(rate=10, period=1.0)
        
        # 7번 요청
        for _ in range(7):
            limiter.acquire()
        
        assert limiter.count == 7
        
        # 3개 더 즉시 가능해야 함
        start = time.time()
        for _ in range(3):
            limiter.acquire()
        elapsed = time.time() - start
        
        assert elapsed < 0.1  # 거의 즉시

    def test_rate_limit_blocking_callback(self):
        """블로킹 콜백 호출 확인"""
        callback_calls = []
        
        def callback():
            callback_calls.append(time.time())
        
        limiter = RateLimiter(rate=2, period=1.0)
        
        # 3번 요청
        for _ in range(3):
            limiter.acquire(blocking=True, blocking_callback=callback)
        
        # 3번째 요청에서 콜백 호출되어야 함
        assert len(callback_calls) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
