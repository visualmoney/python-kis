"""
중급 예제 04: 여러 종목 실시간 모니터링 (대시보드)
Python-KIS 사용 예제

설명:
  - 여러 종목의 가격을 실시간으로 모니터링
  - 가격 변동 알림
  - 간단한 대시보드 표시
  - 상승/하락 추적

실행 조건:
  - config.yaml이 루트에 있어야 함
  - 모의투자 모드 권장 (virtual=true)

사용 모듈:
  - PyKis: 한국투자증권 API
  - SimpleKIS: 초보자 친화 인터페이스
  - time: 폴링 간격 제어
"""

from pykis import create_client
import argparse
from pykis.simple import SimpleKIS
import time
import os
from datetime import datetime
from typing import Dict, List


class StockMonitor:
    """여러 종목을 모니터링하는 클래스"""
    
    def __init__(self, simple_kis: SimpleKIS, symbols: List[str]):
        self.simple = simple_kis
        self.symbols = symbols
        self.prices: Dict = {}
        self.change_alerts: Dict = {}
    
    def fetch_prices(self) -> None:
        """현재 가격을 조회합니다."""
        for symbol in self.symbols:
            try:
                price = self.simple.get_price(symbol)
                if symbol not in self.prices:
                    self.prices[symbol] = {
                        "name": price.name,
                        "current": price.price,
                        "previous": price.price,
                        "high": price.price,
                        "low": price.price,
                    }
                else:
                    self.prices[symbol]["previous"] = self.prices[symbol]["current"]
                    self.prices[symbol]["current"] = price.price
                    self.prices[symbol]["high"] = max(
                        self.prices[symbol]["high"],
                        price.price
                    )
                    self.prices[symbol]["low"] = min(
                        self.prices[symbol]["low"],
                        price.price
                    )
            except Exception as e:
                print(f"⚠️ {symbol} 조회 실패: {e}")
    
    def detect_changes(self) -> None:
        """가격 변동을 감지합니다."""
        for symbol in self.symbols:
            if symbol in self.prices:
                change = self.prices[symbol]["current"] - self.prices[symbol]["previous"]
                if change != 0:
                    self.change_alerts[symbol] = change
    
    def display_dashboard(self) -> None:
        """대시보드를 표시합니다."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n{'=' * 80}")
        print(f"📊 실시간 모니터링 대시보드 [{timestamp}]")
        print(f"{'=' * 80}")
        print()
        print(
            f"{'종목':<10} {'이름':<12} {'현재가':>10} {'변화':>10} "
            f"{'변화율':>10} {'고가':>10} {'저가':>10} {'상태':<6}"
        )
        print("-" * 80)
        
        for symbol in self.symbols:
            if symbol not in self.prices:
                continue
            
            data = self.prices[symbol]
            change = data["current"] - data["previous"]
            change_rate = (change / data["previous"] * 100) if data["previous"] > 0 else 0
            
            # 상태 기호
            if change > 0:
                status = "📈 상승"
            elif change < 0:
                status = "📉 하락"
            else:
                status = "➡️ 보합"
            
            # 매수/매도 신호
            signal = ""
            if symbol in self.change_alerts:
                if self.change_alerts[symbol] > 0:
                    signal = "⬆️"
                else:
                    signal = "⬇️"
            
            print(
                f"{symbol:<10} {data['name']:<12} {data['current']:>10,} "
                f"{change:>10,} {change_rate:>9.2f}% {data['high']:>10,} "
                f"{data['low']:>10,} {status:<6} {signal}"
            )
        
        print()
    
    def run(self, duration: int = 60, interval: int = 5) -> None:
        """모니터링을 실행합니다."""
        start_time = time.time()
        
        print(f"🚀 모니터링 시작 ({duration}초 동안 {interval}초 간격으로 조회)")
        print()
        
        try:
            while time.time() - start_time < duration:
                self.fetch_prices()
                self.detect_changes()
                self.display_dashboard()
                
                elapsed = int(time.time() - start_time)
                remaining = duration - elapsed
                print(f"⏱️ 진행 중... ({elapsed}초 / {duration}초) | 남은 시간: {remaining}초")
                
                time.sleep(interval)
        
        except KeyboardInterrupt:
            print("\n🛑 사용자가 중단했습니다.")
        
        print()
        print("✅ 모니터링 완료!")


def main(config_path: str | None = None, profile: str | None = None) -> None:
    """메인 함수"""
    
    config_path = config_path or os.path.join(os.getcwd(), "config.yaml")
    if not os.path.exists(config_path):
        print(f"❌ {config_path}를 찾을 수 없습니다.")
        return
    
    kis = create_client(config_path, profile=profile)
    simple = SimpleKIS(kis)
    
    print("=" * 80)
    print("Python-KIS 중급 예제 04: 실시간 모니터링 대시보드")
    print("=" * 80)
    print()
    
    # 모니터링할 종목
    symbols = [
        "005930",  # 삼성전자
        "000660",  # SK하이닉스
        "051910",  # LG화학
        "012330",  # 현대모비스
    ]
    
    # 모니터 생성 및 실행
    monitor = StockMonitor(simple, symbols)
    
    print(f"📋 모니터링 종목: {', '.join([f'{sym}' for sym in symbols])}")
    print()
    
    # 60초 동안 5초 간격으로 모니터링
    monitor.run(duration=60, interval=5)
    
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml", help="path to config file")
    parser.add_argument("--profile", help="config profile name (virtual|real)")
    args = parser.parse_args()

    try:
        main(config_path=args.config, profile=args.profile)
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
