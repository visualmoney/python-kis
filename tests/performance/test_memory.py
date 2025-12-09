"""
메모리 프로파일링 테스트

KisObject의 메모리 사용량을 추적합니다.
"""

import pytest
import tracemalloc
from typing import List
from pykis.responses.dynamic import KisObject


class MockData(KisObject):
    """모의 데이터"""
    __fields__ = {
        'id': str,
        'value': int,
        'name': str,
        'data': str,
    }


class MockNested(KisObject):
    """중첩 데이터"""
    __fields__ = {
        'id': str,
        'items': list[MockData],
    }


class MemoryProfile:
    """메모리 프로파일 결과"""
    
    def __init__(self, name: str, peak_kb: float, diff_kb: float, count: int):
        self.name = name
        self.peak_kb = peak_kb
        self.diff_kb = diff_kb
        self.count = count
    
    @property
    def per_item_kb(self) -> float:
        """항목당 메모리 사용량(KB)"""
        if self.count > 0:
            return self.diff_kb / self.count
        return 0.0
    
    def __repr__(self):
        return (
            f"{self.name}: {self.diff_kb:.1f}KB total, "
            f"{self.per_item_kb:.3f}KB/item (peak: {self.peak_kb:.1f}KB)"
        )


class TestMemoryUsage:
    """메모리 사용량 테스트"""

    def test_memory_single_object(self):
        """단일 객체 메모리 사용"""
        tracemalloc.start()
        
        snapshot_before = tracemalloc.take_snapshot()
        
        # 1000개 객체 생성
        objects = []
        for i in range(1000):
            data = {
                'id': f'item_{i}',
                'value': i,
                'name': f'name_{i}',
                'data': f'data_{i}' * 10,  # 약간 큰 문자열
            }
            obj = MockData.transform_(data)
            objects.append(obj)
        
        snapshot_after = tracemalloc.take_snapshot()
        
        # 피크 메모리
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # 메모리 차이 계산
        diff_stats = snapshot_after.compare_to(snapshot_before, 'lineno')
        total_diff = sum(stat.size_diff for stat in diff_stats)
        
        profile = MemoryProfile(
            "단일 객체 (1000개)",
            peak / 1024,
            total_diff / 1024,
            1000
        )
        
        print(f"\n{profile}")
        
        # 기대: 객체당 < 5KB
        assert profile.per_item_kb < 5.0

    def test_memory_nested_objects(self):
        """중첩 객체 메모리 사용"""
        tracemalloc.start()
        
        snapshot_before = tracemalloc.take_snapshot()
        
        # 100개 부모, 각 10개 자식
        objects = []
        for i in range(100):
            data = {
                'id': f'parent_{i}',
                'items': [
                    {
                        'id': f'child_{i}_{j}',
                        'value': j,
                        'name': f'name_{j}',
                        'data': f'data_{j}',
                    }
                    for j in range(10)
                ]
            }
            obj = MockNested.transform_(data)
            objects.append(obj)
        
        snapshot_after = tracemalloc.take_snapshot()
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        diff_stats = snapshot_after.compare_to(snapshot_before, 'lineno')
        total_diff = sum(stat.size_diff for stat in diff_stats)
        
        # 총 객체 수: 100 + (100 * 10) = 1100개
        profile = MemoryProfile(
            "중첩 객체 (100×10=1000개)",
            peak / 1024,
            total_diff / 1024,
            1100
        )
        
        print(f"\n{profile}")
        
        # 기대: 객체당 < 10KB
        assert profile.per_item_kb < 10.0

    def test_memory_large_list(self):
        """대량 리스트 메모리 사용"""
        tracemalloc.start()
        
        snapshot_before = tracemalloc.take_snapshot()
        
        # 1개 부모, 1000개 자식
        data = {
            'id': 'root',
            'items': [
                {
                    'id': f'item_{i}',
                    'value': i,
                    'name': f'name_{i}',
                    'data': f'data_{i}',
                }
                for i in range(1000)
            ]
        }
        
        obj = MockNested.transform_(data)
        
        snapshot_after = tracemalloc.take_snapshot()
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        diff_stats = snapshot_after.compare_to(snapshot_before, 'lineno')
        total_diff = sum(stat.size_diff for stat in diff_stats)
        
        profile = MemoryProfile(
            "대량 리스트 (1×1000=1000개)",
            peak / 1024,
            total_diff / 1024,
            1001
        )
        
        print(f"\n{profile}")
        
        # 기대: 총 사용량 < 5MB
        assert profile.diff_kb < 5000

    def test_memory_leak_check(self):
        """메모리 누수 확인"""
        tracemalloc.start()
        
        # 첫 번째 실행
        snapshot1 = tracemalloc.take_snapshot()
        
        for _ in range(100):
            data = {
                'id': 'test',
                'value': 42,
                'name': 'test',
                'data': 'test' * 100,
            }
            obj = MockData.transform_(data)
            # 참조 해제 (자동)
        
        snapshot2 = tracemalloc.take_snapshot()
        
        # 두 번째 실행 (동일)
        for _ in range(100):
            data = {
                'id': 'test',
                'value': 42,
                'name': 'test',
                'data': 'test' * 100,
            }
            obj = MockData.transform_(data)
        
        snapshot3 = tracemalloc.take_snapshot()
        tracemalloc.stop()
        
        # 첫 실행과 두 번째 실행의 메모리 증가량
        diff_1_2 = snapshot2.compare_to(snapshot1, 'lineno')
        diff_2_3 = snapshot3.compare_to(snapshot2, 'lineno')
        
        size_1_2 = sum(stat.size_diff for stat in diff_1_2)
        size_2_3 = sum(stat.size_diff for stat in diff_2_3)
        
        print(f"\n첫 실행: {size_1_2 / 1024:.1f}KB")
        print(f"두 번째 실행: {size_2_3 / 1024:.1f}KB")
        
        # 누수가 없다면 두 번째 실행은 첫 실행보다 작아야 함
        # (가비지 컬렉션으로 해제됨)
        # 또는 비슷해야 함 (일정한 메모리 사용)
        assert abs(size_2_3 - size_1_2) < abs(size_1_2) * 0.5

    def test_memory_gc_effectiveness(self):
        """가비지 컬렉션 효과"""
        import gc
        
        tracemalloc.start()
        
        # 대량 생성
        snapshot1 = tracemalloc.take_snapshot()
        
        objects = []
        for i in range(1000):
            data = {
                'id': f'item_{i}',
                'value': i,
                'name': f'name_{i}' * 10,
                'data': f'data_{i}' * 100,
            }
            obj = MockData.transform_(data)
            objects.append(obj)
        
        snapshot2 = tracemalloc.take_snapshot()
        
        # 참조 해제
        objects.clear()
        gc.collect()
        
        snapshot3 = tracemalloc.take_snapshot()
        tracemalloc.stop()
        
        # 생성 시 증가량
        diff_create = snapshot2.compare_to(snapshot1, 'lineno')
        size_create = sum(stat.size_diff for stat in diff_create)
        
        # 해제 시 감소량
        diff_clear = snapshot3.compare_to(snapshot2, 'lineno')
        size_clear = sum(stat.size_diff for stat in diff_clear)
        
        print(f"\n생성: +{size_create / 1024:.1f}KB")
        print(f"해제: {size_clear / 1024:.1f}KB")
        
        # 대부분 해제되어야 함 (70% 이상)
        assert abs(size_clear) >= abs(size_create) * 0.7

    def test_memory_growth_pattern(self):
        """메모리 증가 패턴"""
        tracemalloc.start()
        
        snapshots = []
        counts = [100, 500, 1000, 5000]
        
        for count in counts:
            objects = []
            for i in range(count):
                data = {
                    'id': f'item_{i}',
                    'value': i,
                    'name': f'name_{i}',
                    'data': f'data_{i}',
                }
                obj = MockData.transform_(data)
                objects.append(obj)
            
            snapshot = tracemalloc.take_snapshot()
            snapshots.append(snapshot)
            
            # 참조 해제
            objects.clear()
        
        tracemalloc.stop()
        
        # 각 단계별 메모리 증가량
        print("\n=== 메모리 증가 패턴 ===")
        for i in range(len(snapshots) - 1):
            diff = snapshots[i + 1].compare_to(snapshots[i], 'lineno')
            size = sum(stat.size_diff for stat in diff)
            
            count_diff = counts[i + 1] - counts[i]
            per_item = size / count_diff if count_diff > 0 else 0
            
            print(f"{counts[i]} → {counts[i+1]}: {size / 1024:.1f}KB "
                  f"({per_item / 1024:.3f}KB/item)")
        
        # 선형 증가 확인 (마지막이 첫 번째의 약 50배)
        # (5000-1000)/(1000-100) = 4000/900 ≈ 4.4배
        last_diff = snapshots[-1].compare_to(snapshots[-2], 'lineno')
        first_diff = snapshots[1].compare_to(snapshots[0], 'lineno')
        
        last_size = sum(stat.size_diff for stat in last_diff)
        first_size = sum(stat.size_diff for stat in first_diff)
        
        # 대략 비례 (3~6배 사이)
        if first_size > 0:
            ratio = abs(last_size) / abs(first_size)
            assert 3.0 <= ratio <= 6.0


class TestMemoryComparison:
    """메모리 사용량 비교"""

    def test_compare_creation_methods(self):
        """생성 방법별 메모리 비교"""
        import gc
        
        # 1. transform_() 사용
        tracemalloc.start()
        gc.collect()
        
        snapshot1 = tracemalloc.take_snapshot()
        
        objects1 = []
        for i in range(1000):
            data = {
                'id': f'item_{i}',
                'value': i,
                'name': f'name_{i}',
                'data': f'data_{i}',
            }
            obj = MockData.transform_(data)
            objects1.append(obj)
        
        snapshot2 = tracemalloc.take_snapshot()
        
        diff1 = snapshot2.compare_to(snapshot1, 'lineno')
        size1 = sum(stat.size_diff for stat in diff1)
        
        # 해제
        objects1.clear()
        gc.collect()
        
        # 2. 직접 dict 저장
        snapshot3 = tracemalloc.take_snapshot()
        
        objects2 = []
        for i in range(1000):
            data = {
                'id': f'item_{i}',
                'value': i,
                'name': f'name_{i}',
                'data': f'data_{i}',
            }
            objects2.append(data)
        
        snapshot4 = tracemalloc.take_snapshot()
        tracemalloc.stop()
        
        diff2 = snapshot4.compare_to(snapshot3, 'lineno')
        size2 = sum(stat.size_diff for stat in diff2)
        
        print(f"\nKisObject: {size1 / 1024:.1f}KB")
        print(f"Dict: {size2 / 1024:.1f}KB")
        print(f"Overhead: {(size1 - size2) / 1024:.1f}KB "
              f"({((size1 / size2 - 1) * 100) if size2 > 0 else 0:.1f}%)")
        
        # KisObject가 dict보다 크지만, 3배 이하여야 함
        if size2 > 0:
            assert size1 / size2 < 3.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
