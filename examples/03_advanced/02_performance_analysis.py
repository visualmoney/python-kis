"""
고급 예제 02: 거래 성과 분석 및 리포팅
Python-KIS 사용 예제

설명:
  - 거래 기록 분석
  - 수익률 계산
  - 성과 지표 (Sharpe ratio, max drawdown 개념)
  - CSV/JSON 리포트 생성

실행 조건:
  - config.yaml이 루트에 있어야 함

사용 모듈:
  - PyKis: 한국투자증권 API
  - json/csv: 리포팅
"""

import json
import csv
from datetime import datetime, timedelta
from typing import List, Dict
import os


class PerformanceAnalyzer:
    """거래 성과를 분석하는 클래스"""
    
    def __init__(self):
        # 시뮬레이션용 거래 데이터
        self.trades: List[Dict] = [
            {
                "date": "2025-12-01",
                "symbol": "005930",
                "side": "buy",
                "qty": 10,
                "price": 65000,
                "amount": 650000,
            },
            {
                "date": "2025-12-05",
                "symbol": "005930",
                "side": "sell",
                "qty": 10,
                "price": 67000,
                "amount": 670000,
            },
            {
                "date": "2025-12-08",
                "symbol": "000660",
                "side": "buy",
                "qty": 20,
                "price": 120000,
                "amount": 2400000,
            },
            {
                "date": "2025-12-15",
                "symbol": "000660",
                "side": "sell",
                "qty": 20,
                "price": 125000,
                "amount": 2500000,
            },
        ]
    
    def analyze_trades(self) -> Dict:
        """거래를 분석합니다"""
        
        # 매수/매도 페어링
        pairs = []
        open_positions = {}
        
        for trade in self.trades:
            symbol = trade["symbol"]
            
            if trade["side"] == "buy":
                if symbol not in open_positions:
                    open_positions[symbol] = []
                open_positions[symbol].append(trade)
            
            elif trade["side"] == "sell":
                if symbol in open_positions and open_positions[symbol]:
                    buy_trade = open_positions[symbol].pop(0)
                    
                    # 손익 계산
                    buy_cost = buy_trade["amount"]
                    sell_revenue = trade["amount"]
                    profit = sell_revenue - buy_cost
                    profit_rate = (profit / buy_cost) * 100
                    
                    pairs.append({
                        "symbol": symbol,
                        "buy_date": buy_trade["date"],
                        "buy_price": buy_trade["price"],
                        "buy_qty": buy_trade["qty"],
                        "sell_date": trade["date"],
                        "sell_price": trade["price"],
                        "sell_qty": trade["qty"],
                        "profit": profit,
                        "profit_rate": profit_rate,
                    })
        
        return {
            "pairs": pairs,
            "open_positions": open_positions,
        }
    
    def calculate_metrics(self, analysis: Dict) -> Dict:
        """성과 지표를 계산합니다"""
        
        pairs = analysis["pairs"]
        
        if not pairs:
            return {
                "total_trades": 0,
                "total_profit": 0,
                "avg_profit_rate": 0,
            }
        
        total_profit = sum(p["profit"] for p in pairs)
        avg_profit_rate = sum(p["profit_rate"] for p in pairs) / len(pairs)
        winning_trades = len([p for p in pairs if p["profit"] > 0])
        losing_trades = len([p for p in pairs if p["profit"] < 0])
        win_rate = (winning_trades / len(pairs) * 100) if pairs else 0
        
        return {
            "total_trades": len(pairs),
            "total_profit": total_profit,
            "avg_profit_rate": avg_profit_rate,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "max_profit": max((p["profit"] for p in pairs), default=0),
            "max_loss": min((p["profit"] for p in pairs), default=0),
        }
    
    def generate_report(self, analysis: Dict, metrics: Dict) -> str:
        """리포트를 생성합니다"""
        
        report = []
        report.append("=" * 80)
        report.append("거래 성과 분석 리포트")
        report.append("=" * 80)
        report.append(f"분석 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 주요 지표
        report.append("📊 주요 지표")
        report.append("-" * 80)
        report.append(f"총 거래 쌍: {metrics['total_trades']}개")
        report.append(f"총 손익: {metrics['total_profit']:,}원")
        report.append(f"평균 수익률: {metrics['avg_profit_rate']:+.2f}%")
        report.append(f"승률: {metrics['win_rate']:.1f}% ({metrics['winning_trades']}승 {metrics['losing_trades']}패)")
        report.append(f"최대 수익: {metrics['max_profit']:,}원")
        report.append(f"최대 손실: {metrics['max_loss']:,}원")
        report.append("")
        
        # 거래 상세
        if analysis["pairs"]:
            report.append("📝 거래 상세")
            report.append("-" * 80)
            report.append(f"{'종목':<10} {'매수가':>10} {'매도가':>10} {'손익':>10} {'수익률':>10}")
            report.append("-" * 80)
            
            for pair in analysis["pairs"]:
                profit_symbol = "✓" if pair["profit"] > 0 else "✗"
                report.append(
                    f"{pair['symbol']:<10} {pair['buy_price']:>10,} "
                    f"{pair['sell_price']:>10,} {pair['profit']:>10,} "
                    f"{pair['profit_rate']:>9.2f}% {profit_symbol}"
                )
        
        report.append("")
        report.append("✅ 리포트 생성 완료")
        
        return "\n".join(report)
    
    def save_report(self, report: str, filename: str = "performance_report.txt") -> None:
        """리포트를 파일로 저장합니다"""
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report)
        
        print(f"💾 리포트 저장: {filename}")
    
    def export_to_json(self, analysis: Dict, filename: str = "trades.json") -> None:
        """거래 데이터를 JSON으로 내보냅니다"""
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(analysis["pairs"], f, indent=2, ensure_ascii=False)
        
        print(f"💾 JSON 내보내기: {filename}")
    
    def export_to_csv(self, analysis: Dict, filename: str = "trades.csv") -> None:
        """거래 데이터를 CSV로 내보냅니다"""
        
        if not analysis["pairs"]:
            print("⚠️ 내보낼 데이터가 없습니다.")
            return
        
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=analysis["pairs"][0].keys())
            writer.writeheader()
            writer.writerows(analysis["pairs"])
        
        print(f"💾 CSV 내보내기: {filename}")


def main() -> None:
    """메인 함수"""
    
    print("=" * 80)
    print("Python-KIS 고급 예제 02: 거래 성과 분석 및 리포팅")
    print("=" * 80)
    print()
    
    # 분석기 생성
    analyzer = PerformanceAnalyzer()
    
    # 1단계: 거래 분석
    print("1️⃣ 거래 분석 중...")
    analysis = analyzer.analyze_trades()
    print(f"   총 거래 쌍: {len(analysis['pairs'])}개")
    print()
    
    # 2단계: 성과 지표 계산
    print("2️⃣ 성과 지표 계산 중...")
    metrics = analyzer.calculate_metrics(analysis)
    print()
    
    # 3단계: 리포트 생성
    print("3️⃣ 리포트 생성 중...")
    report = analyzer.generate_report(analysis, metrics)
    print(report)
    print()
    
    # 4단계: 파일 저장
    print("4️⃣ 결과 저장 중...")
    analyzer.save_report(report)
    analyzer.export_to_json(analysis)
    analyzer.export_to_csv(analysis)
    print()
    
    print("✅ 거래 성과 분석 완료!")
    print()
    print("💡 생성된 파일:")
    print("   - performance_report.txt: 텍스트 리포트")
    print("   - trades.json: JSON 형식 거래 데이터")
    print("   - trades.csv: CSV 형식 거래 데이터")
    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
