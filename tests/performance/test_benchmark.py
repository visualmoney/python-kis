"""
성능 벤치마크 테스트

KisObject.transform_()의 대량 변환 성능을 측정합니다.
"""

import pytest
import time
from typing import List
from pykis.responses.dynamic import KisObject


class MockPrice(KisObject):
    """모의 가격 응답"""
    __fields__ = {
        'symbol': str,
        'price': int,
        'volume': int,
        'timestamp': str,
        'market': str,
    }


class MockQuote(KisObject):
    """모의 시세 응답"""
    __fields__ = {
        'symbol': str,
        'name': str,
        'current_price': int,
        'high': int,
        'low': int,
        'volume': int,
        'prices': list[MockPrice],
    }


class BenchmarkResult:
    """벤치마크 결과"""
    
    def __init__(self, name: str, elapsed: float, count: int):
        self.name = name
        self.elapsed = elapsed
        self.count = count
    
    @property
    def ops_per_second(self) -> float:
        """초당 연산 수"""
        if self.elapsed > 0:
            return self.count / self.elapsed
        return 0.0
    
    @property
    def avg_time_ms(self) -> float:
        """평균 시간(ms)"""
        if self.count > 0:
            return (self.elapsed / self.count) * 1000
        return 0.0
    
    def __repr__(self):
        return (
            f"{self.name}: {self.count} ops in {self.elapsed:.3f}s "
            f"({self.ops_per_second:.1f} ops/s, {self.avg_time_ms:.3f}ms/op)"
        )


class TestTransformBenchmark:
    """KisObject.transform_() 벤치마크"""

    def test_benchmark_simple_transform(self):
        """단순 객체 변환 벤치마크"""
        data = {
            'symbol': '005930',
            'price': 70000,
            'volume': 1000000,
            'timestamp': '20240101090000',
            'market': 'KRX',
        }
        
        count = 1000
        start = time.time()
        
        for _ in range(count):
            result = MockPrice.transform_(data)
            assert result.symbol == '005930'
        
        elapsed = time.time() - start
        benchmark = BenchmarkResult("단순 변환", elapsed, count)
        
        print(f"\n{benchmark}")
        
        # 기대: 1000개 변환 < 0.5초 (2000+ ops/s)
        assert benchmark.ops_per_second > 2000

    def test_benchmark_nested_transform(self):
        """중첩 객체 변환 벤치마크"""
        data = {
            'symbol': '005930',
            'name': '삼성전자',
            'current_price': 70000,
            'high': 71000,
            'low': 69000,
            'volume': 5000000,
            'prices': [
                {
                    'symbol': '005930',
                    'price': 70000 + i * 100,
                    'volume': 100000 - i * 1000,
                    'timestamp': f'2024010109{i:02d}00',
                    'market': 'KRX',
                }
                for i in range(10)
            ]
        }
        
        count = 100
        start = time.time()
        
        for _ in range(count):
            result = MockQuote.transform_(data)
            assert len(result.prices) == 10
        
        elapsed = time.time() - start
        benchmark = BenchmarkResult("중첩 변환 (10개 자식)", elapsed, count)
        
        print(f"\n{benchmark}")
        
        # 기대: 100개 변환 < 0.5초 (200+ ops/s)
        assert benchmark.ops_per_second > 200

    def test_benchmark_large_list_transform(self):
        """대량 리스트 변환 벤치마크"""
        data = {
            'symbol': '005930',
            'name': '삼성전자',
            'current_price': 70000,
            'high': 71000,
            'low': 69000,
            'volume': 5000000,
            'prices': [
                {
                    'symbol': '005930',
                    'price': 70000 + i,
                    'volume': 100000,
                    'timestamp': '20240101090000',
                    'market': 'KRX',
                }
                for i in range(100)
            ]
        }
        
        count = 10
        start = time.time()
        
        for _ in range(count):
            result = MockQuote.transform_(data)
            assert len(result.prices) == 100
        
        elapsed = time.time() - start
        benchmark = BenchmarkResult("대량 리스트 (100개)", elapsed, count)
        
        print(f"\n{benchmark}")
        
        # 기대: 10개 변환 < 1.0초 (10+ ops/s)
        assert benchmark.ops_per_second > 10

    def test_benchmark_batch_transform(self):
        """배치 변환 벤치마크"""
        prices = [
            {
                'symbol': f'{1000 + i:06d}',
                'price': 50000 + i * 100,
                'volume': 100000 + i * 1000,
                'timestamp': '20240101090000',
                'market': 'KRX',
            }
            for i in range(100)
        ]
        
        start = time.time()
        
        results = [MockPrice.transform_(price) for price in prices]
        
        elapsed = time.time() - start
        benchmark = BenchmarkResult("배치 변환 (100개)", elapsed, len(prices))
        
        print(f"\n{benchmark}")
        
        assert len(results) == 100
        # 기대: 100개 < 0.1초 (1000+ ops/s)
        assert benchmark.ops_per_second > 1000

    def test_benchmark_deep_nesting(self):
        """깊은 중첩 벤치마크"""
        class Level3(KisObject):
            __fields__ = {'value': int, 'name': str}
        
        class Level2(KisObject):
            __fields__ = {'items': list[Level3], 'count': int}
        
        class Level1(KisObject):
            __fields__ = {'data': Level2, 'id': str}
        
        data = {
            'id': 'root',
            'data': {
                'count': 5,
                'items': [
                    {'value': i, 'name': f'item_{i}'}
                    for i in range(5)
                ]
            }
        }
        
        count = 100
        start = time.time()
        
        for _ in range(count):
            result = Level1.transform_(data)
            assert result.data.count == 5
        
        elapsed = time.time() - start
        benchmark = BenchmarkResult("깊은 중첩 (3레벨, 5개)", elapsed, count)
        
        print(f"\n{benchmark}")
        
        # 기대: 100개 < 0.3초 (300+ ops/s)
        assert benchmark.ops_per_second > 300

    def test_benchmark_optional_fields(self):
        """선택 필드 벤치마크"""
        class OptionalData(KisObject):
            __fields__ = {
                'required': str,
                'optional1': int | None,
                'optional2': str | None,
                'optional3': float | None,
            }
        
        # 일부 필드만 있는 데이터
        data = {
            'required': 'test',
            'optional1': 42,
            # optional2, optional3 없음
        }
        
        count = 1000
        start = time.time()
        
        for _ in range(count):
            result = OptionalData.transform_(data)
            assert result.required == 'test'
        
        elapsed = time.time() - start
        benchmark = BenchmarkResult("선택 필드", elapsed, count)
        
        print(f"\n{benchmark}")
        
        # 기대: 1000개 < 0.5초 (2000+ ops/s)
        assert benchmark.ops_per_second > 2000

    def test_benchmark_comparison(self):
        """다양한 시나리오 비교 벤치마크"""
        scenarios = []
        
        # 1. 단순
        simple_data = {
            'symbol': '005930',
            'price': 70000,
            'volume': 1000000,
            'timestamp': '20240101090000',
            'market': 'KRX',
        }
        
        count = 500
        start = time.time()
        for _ in range(count):
            MockPrice.transform_(simple_data)
        scenarios.append(BenchmarkResult("단순 (5필드)", time.time() - start, count))
        
        # 2. 중첩 (10개)
        nested_data = {
            'symbol': '005930',
            'name': '삼성전자',
            'current_price': 70000,
            'high': 71000,
            'low': 69000,
            'volume': 5000000,
            'prices': [
                {
                    'symbol': '005930',
                    'price': 70000 + i,
                    'volume': 100000,
                    'timestamp': '20240101090000',
                    'market': 'KRX',
                }
                for i in range(10)
            ]
        }
        
        count = 100
        start = time.time()
        for _ in range(count):
            MockQuote.transform_(nested_data)
        scenarios.append(BenchmarkResult("중첩 (10개)", time.time() - start, count))
        
        # 3. 대량 (100개)
        large_data = {
            'symbol': '005930',
            'name': '삼성전자',
            'current_price': 70000,
            'high': 71000,
            'low': 69000,
            'volume': 5000000,
            'prices': [
                {
                    'symbol': '005930',
                    'price': 70000 + i,
                    'volume': 100000,
                    'timestamp': '20240101090000',
                    'market': 'KRX',
                }
                for i in range(100)
            ]
        }
        
        count = 10
        start = time.time()
        for _ in range(count):
            MockQuote.transform_(large_data)
        scenarios.append(BenchmarkResult("대량 (100개)", time.time() - start, count))
        
        # 결과 출력
        print("\n=== 벤치마크 비교 ===")
        for scenario in scenarios:
            print(scenario)
        
        # 모든 시나리오가 기대치 충족
        assert all(s.ops_per_second > 10 for s in scenarios)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
