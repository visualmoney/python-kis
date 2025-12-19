"""
중급 예제 05: 고급 주문 타입 (지정가, 시장가, 조건부)
Python-KIS 사용 예제

설명:
  - 지정가 주문 (limit order)
  - 시장가 주문 (market order)
  - 분할 매수 전략 (dollar-cost averaging)
  - 손절/익절 설정

실행 조건:
  - config.yaml이 루트에 있어야 함
  - 모의투자 모드 권장 (virtual=true)
  - 실계좌 주문 시: ALLOW_LIVE_TRADES=1 환경변수 필수

사용 모듈:
  - PyKis: 한국투자증권 API
  - SimpleKIS: 초보자 친화 인터페이스
"""

from pykis import create_client
import argparse
from pykis.simple import SimpleKIS
import os
from typing import List, Tuple


class AdvancedOrderer:
    """고급 주문 전략을 관리하는 클래스"""
    
    def __init__(self, simple_kis: SimpleKIS):
        self.simple = simple_kis
        self.orders: List = []
    
    def limit_order(
        self, symbol: str, side: str, qty: int, limit_price: int
    ) -> Tuple[bool, str]:
        """
        지정가 주문을 실행합니다.
        
        Args:
            symbol: 종목 코드
            side: 'buy' 또는 'sell'
            qty: 수량
            limit_price: 지정가
        
        Returns:
            (성공 여부, 주문 ID 또는 메시지)
        """
        try:
            # 현재 가격 확인
            price = self.simple.get_price(symbol)
            current_price = price.price
            
            # 매수 시 현재가보다 낮은 가격, 매도 시 높은 가격 추천
            if side == "buy":
                if limit_price >= current_price:
                    print(f"⚠️ 주의: 지정가({limit_price:,}원)가 현재가({current_price:,}원) 이상입니다.")
                    print("   지정가가 높으면 즉시 체결될 수 있습니다.")
            elif side == "sell":
                if limit_price <= current_price:
                    print(f"⚠️ 주의: 지정가({limit_price:,}원)가 현재가({current_price:,}원) 이하입니다.")
                    print("   지정가가 낮으면 즉시 체결될 수 있습니다.")
            
            # 주문 실행
            order = self.simple.place_order(
                symbol=symbol,
                side=side,
                qty=qty,
                price=limit_price
            )
            
            self.orders.append({
                "type": "limit",
                "order_id": order.order_id,
                "symbol": symbol,
                "side": side,
                "qty": qty,
                "price": limit_price,
            })
            
            return True, order.order_id
        
        except Exception as e:
            return False, str(e)
    
    def market_order(self, symbol: str, side: str, qty: int) -> Tuple[bool, str]:
        """
        시장가 주문을 실행합니다.
        
        Args:
            symbol: 종목 코드
            side: 'buy' 또는 'sell'
            qty: 수량
        
        Returns:
            (성공 여부, 주문 ID 또는 메시지)
        """
        try:
            price = self.simple.get_price(symbol)
            print(f"ℹ️ 시장가 주문: 현재 {price.name}의 시장가로 즉시 체결됩니다.")
            
            # 시장가 주문 (price 없음 또는 현재가 사용)
            order = self.simple.place_order(
                symbol=symbol,
                side=side,
                qty=qty,
                price=None  # price 없으면 시장가
            )
            
            self.orders.append({
                "type": "market",
                "order_id": order.order_id,
                "symbol": symbol,
                "side": side,
                "qty": qty,
                "price": price.price,
            })
            
            return True, order.order_id
        
        except Exception as e:
            return False, str(e)
    
    def dollar_cost_averaging(
        self, symbol: str, total_amount: int, num_tranches: int
    ) -> List[Tuple[bool, str]]:
        """
        분할 매수 전략 (Dollar-Cost Averaging)을 실행합니다.
        
        예: 1,000,000원을 5번에 나누어 매수
        
        Args:
            symbol: 종목 코드
            total_amount: 총 매수액
            num_tranches: 분할 횟수
        
        Returns:
            각 주문의 (성공 여부, 주문 ID) 튜플 리스트
        """
        results = []
        amount_per_tranche = total_amount // num_tranches
        
        print(f"🤖 분할 매수 전략 시작")
        print(f"   총액: {total_amount:,}원")
        print(f"   횟수: {num_tranches}회")
        print(f"   회당: {amount_per_tranche:,}원")
        print()
        
        for i in range(num_tranches):
            try:
                price = self.simple.get_price(symbol)
                current_price = price.price
                qty = amount_per_tranche // current_price
                
                if qty < 1:
                    print(f"⚠️ {i+1}회: 수량 부족 (금액: {amount_per_tranche:,}원 < 주가: {current_price:,}원)")
                    results.append((False, "수량 부족"))
                    continue
                
                print(f"📍 {i+1}/{num_tranches} 회차:")
                print(f"   현재가: {current_price:,}원")
                print(f"   매수액: {amount_per_tranche:,}원")
                print(f"   수량: {qty}주")
                
                success, result = self.limit_order(
                    symbol=symbol,
                    side="buy",
                    qty=qty,
                    limit_price=current_price
                )
                
                if success:
                    print(f"   ✅ 주문 ID: {result}")
                else:
                    print(f"   ❌ 실패: {result}")
                
                results.append((success, result))
                print()
            
            except Exception as e:
                print(f"   ❌ 오류: {e}")
                results.append((False, str(e)))
        
        return results
    
    def stop_loss_and_take_profit(
        self, symbol: str, qty: int, buy_price: int,
        stop_loss_price: int, take_profit_price: int
    ) -> None:
        """
        손절/익절 설정 시뮬레이션입니다.
        
        실제로는 broker의 조건부 주문 기능을 사용해야 합니다.
        
        Args:
            symbol: 종목 코드
            qty: 수량
            buy_price: 매수가
            stop_loss_price: 손절가 (하한)
            take_profit_price: 익절가 (상한)
        """
        print(f"🛡️ 손절/익절 설정")
        print(f"   종목: {symbol}")
        print(f"   수량: {qty}주")
        print(f"   매수가: {buy_price:,}원")
        print(f"   손절가: {stop_loss_price:,}원 (손실: {(buy_price - stop_loss_price) * qty:,}원)")
        print(f"   익절가: {take_profit_price:,}원 (수익: {(take_profit_price - buy_price) * qty:,}원)")
        print()
        print("⚠️ 주의:")
        print("   SimpleKIS는 조건부 주문을 지원하지 않습니다.")
        print("   실제 거래 시에는 PyKis의 고급 주문 API를 사용하세요.")
        print("   또는 별도의 모니터링 로직으로 가격을 감시하세요.")


def main(config_path: str | None = None, profile: str | None = None) -> None:
    """메인 함수"""

    config_path = config_path or os.path.join(os.getcwd(), "config.yaml")
    if not os.path.exists(config_path):
        print(f"❌ {config_path}를 찾을 수 없습니다.")
        return

    kis = create_client(config_path, profile=profile)
    simple = SimpleKIS(kis)
    orderer = AdvancedOrderer(simple)
    
    print("=" * 70)
    print("Python-KIS 중급 예제 05: 고급 주문 타입")
    print("=" * 70)
    print()
    
    symbol = "005930"  # 삼성전자
    
    # 1. 현재 가격 확인
    print(f"📊 {symbol} 현재 시세 확인 중...")
    price = simple.get_price(symbol)
    print(f"   {price.name}: {price.price:,}원")
    print()
    
    # 2. 지정가 주문 예제
    print("1️⃣ 지정가 주문 (Limit Order)")
    print("-" * 70)
    limit_price = price.price - 1000  # 현재가보다 1,000원 낮은 가격
    print(f"매수 지정가: {limit_price:,}원")
    success, order_id = orderer.limit_order(
        symbol=symbol,
        side="buy",
        qty=1,
        limit_price=limit_price
    )
    if success:
        print(f"✅ 주문 완료: {order_id}")
    else:
        print(f"❌ 주문 실패: {order_id}")
    print()
    
    # 3. 분할 매수 예제
    print("2️⃣ 분할 매수 전략 (Dollar-Cost Averaging)")
    print("-" * 70)
    results = orderer.dollar_cost_averaging(
        symbol=symbol,
        total_amount=1_000_000,  # 100만원
        num_tranches=5  # 5회 분할
    )
    success_count = sum(1 for success, _ in results if success)
    print(f"📊 결과: {success_count}/{len(results)} 주문 성공")
    print()
    
    # 4. 손절/익절 설정 예제
    print("3️⃣ 손절/익절 설정")
    print("-" * 70)
    orderer.stop_loss_and_take_profit(
        symbol=symbol,
        qty=1,
        buy_price=65000,
        stop_loss_price=63000,
        take_profit_price=70000
    )
    print()
    
    # 5. 주문 내역 표시
    print("4️⃣ 주문 내역")
    print("-" * 70)
    if orderer.orders:
        print(f"{'타입':<10} {'종목':<10} {'매매':<6} {'수량':>6} {'가격':>10}")
        print("-" * 70)
        for order in orderer.orders:
            print(
                f"{order['type']:<10} {order['symbol']:<10} "
                f"{order['side']:<6} {order['qty']:>6} {order['price']:>10,}"
            )
    else:
        print("주문 내역 없음")
    print()
    
    print("✅ 고급 주문 예제 완료!")
    print()
    print("💡 팁:")
    print("   - 지정가 주문: 원하는 가격에 체결되기를 기다림 (체결 보장 X)")
    print("   - 시장가 주문: 현재가에 즉시 체결 (체결 보장 O)")
    print("   - 분할 매수: 평균 매수가 낮춤, 리스크 분산")
    print("   - 손절/익절: PyKis의 고급 API 또는 별도 모니터링 필요")
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
