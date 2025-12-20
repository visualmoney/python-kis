"""
# FAQ (자주 묻는 질문)

PyKIS 사용 중 자주 묻는 질문과 답변입니다.

## 설치 및 설정

### Q1: PyKIS를 설치하려면 어떻게 해야 하나요?

A: 다음 명령어로 설치할 수 있습니다.

```bash
pip install pykis
```

또는 poetry를 사용하는 경우:

```bash
poetry add pykis
```

### Q2: API 키(AppKey, AppSecret)는 어디서 얻을 수 있나요?

A: 한국투자증권 공식 웹사이트에서 다음 단계를 따르세요:

1. [한국투자증권 API 신청 페이지](https://www.truefriend.com) 방문
2. 로그인 후 "OpenAPI" 메뉴 선택
3. API 인증서 신청 (실명 인증 필요)
4. 발급받은 AppKey와 AppSecret 확인

⚠️ **보안 주의**: API 키를 GitHub에 올리지 않도록 주의하세요.
환경 변수나 `.gitignore`로 관리되는 `config.yaml`에 저장하세요.

### Q3: 모의 계좌(Virtual Trading)에서 테스트할 수 있나요?

A: 네, 가능합니다. 두 가지 방법이 있습니다:

**방법 1: 환경 변수 사용**
```bash
export PYKIS_REAL_TRADING=false  # Linux/macOS
set PYKIS_REAL_TRADING=false     # Windows CMD
$env:PYKIS_REAL_TRADING = "false" # Windows PowerShell
```

**방법 2: 코드에서 설정**
```python
from pykis import PyKis

kis = PyKis(
    id="YOUR_ID",
    account="YOUR_ACCOUNT",
    appkey="YOUR_APPKEY",
    secretkey="YOUR_SECRETKEY",
    virtual=True  # 모의 거래 사용
)
```

### Q4: "401 Unauthorized" 에러가 발생합니다.

A: 다음을 확인하세요:

1. **AppKey와 AppSecret이 정확한가요?**
   ```python
   print(f"AppKey: {kis.account.appkey}")  # 마스킹됨
   print(f"Account: {kis.account.account}")
   ```

2. **토큰이 만료되었나요?**
   ```python
   # 토큰 자동 갱신
   kis.authenticate()
   ```

3. **모의 계좌와 실전 계좌를 혼동하지 않았나요?**
   - 모의: `virtual=True` 설정
   - 실전: `virtual=False` (기본값)

### Q5: "429 Too Many Requests" 에러가 발생합니다.

A: API 호출 제한을 초과했습니다. 해결 방법:

```python
from pykis.utils.retry import with_retry

@with_retry(max_retries=5, initial_delay=2.0)
def fetch_quote(symbol):
    return kis.stock(symbol).quote()

# 자동 재시도 (exponential backoff 적용)
quote = fetch_quote("005930")
```

**또는 직접 대기:**
```python
import time
time.sleep(5)  # 5초 대기 후 재시도
```

---

## 시세 조회

### Q6: 특정 종목의 현재 시세를 조회하려면?

A: 다음과 같이 조회할 수 있습니다:

```python
from pykis import PyKis

kis = PyKis(...)
quote = kis.stock("005930").quote()  # 삼성전자

print(f"종목명: {quote.name}")
print(f"현재가: {quote.price:,}원")
print(f"변동: {quote.change}원 ({quote.change_rate:.2f}%)")
print(f"매도/매수호가: {quote.ask_price}/{quote.bid_price}")
```

### Q7: 여러 종목의 시세를 동시에 조회하려면?

A: 루프를 사용하거나 비동기 처리를 활용하세요:

```python
# 방법 1: 간단한 루프
symbols = ["005930", "000660", "051910"]
for symbol in symbols:
    quote = kis.stock(symbol).quote()
    print(f"{quote.name}: {quote.price:,}원")

# 방법 2: 비동기 (더 빠름)
import asyncio

async def fetch_quotes(symbols):
    tasks = [kis.stock(s).quote_async() for s in symbols]
    return await asyncio.gather(*tasks)

quotes = asyncio.run(fetch_quotes(symbols))
```

### Q8: 실시간 시세 업데이트를 받으려면?

A: WebSocket을 사용하세요:

```python
from pykis import PyKis

kis = PyKis(...)

def on_quote(quote):
    print(f"{quote.name}: {quote.price:,}원")

# 특정 종목 실시간 구독
kis.stock("005930").subscribe_quote(on_quote)

# 또는 전체 시장 구독
kis.subscribe_quotes(
    symbols=["005930", "000660"],
    on_quote=on_quote,
    on_error=lambda e: print(f"에러: {e}")
)
```

---

## 주문

### Q9: 주문을 어떻게 실행하나요?

A: 다음과 같이 주문할 수 있습니다:

```python
from pykis import PyKis

kis = PyKis(...)

# 매수
order = kis.stock("005930").buy(
    price=65000,  # 매수 가격
    qty=10,       # 수량
    order_type="limit"  # 지정가 주문
)

print(f"주문번호: {order.order_number}")
print(f"상태: {order.status}")

# 매도
sell_order = kis.stock("005930").sell(
    price=66000,
    qty=10
)
```

### Q10: 주문을 취소하려면?

A: 주문번호를 사용하여 취소할 수 있습니다:

```python
# 주문 취소
order_number = "123456"
kis.account().cancel_order(order_number)

# 또는 주문 객체에서 직접
order = kis.stock("005930").buy(65000, 10)
order.cancel()
```

### Q11: 실시간 주문 상태를 모니터링하려면?

A: WebSocket 구독으로 실시간 알림을 받을 수 있습니다:

```python
def on_order_status(order):
    print(f"주문 {order.order_number}: {order.status}")
    print(f"체결: {order.filled_qty}/{order.qty}")

kis.subscribe_orders(on_order_status)
```

---

## 계좌 관리

### Q12: 보유 종목 리스트와 잔고를 확인하려면?

A: 다음과 같이 확인할 수 있습니다:

```python
from pykis import PyKis

kis = PyKis(...)

# 잔고 조회
balance = kis.account().balance()

print(f"현금: {balance.cash:,}원")
print(f"예수금: {balance.deposits}")

# 보유 종목 조회
stocks = balance.stocks
for stock in stocks:
    print(f"{stock.name}: {stock.qty}주 @ {stock.price:,}원")
    print(f"평가: {stock.valuation:,}원")
```

### Q13: 총 자산과 수익률을 계산하려면?

A: 다음과 같이 계산할 수 있습니다:

```python
balance = kis.account().balance()

# 계산
total_investment = sum(s.quantity * s.avg_price for s in balance.stocks)
total_valuation = sum(s.quantity * s.price for s in balance.stocks)
total_assets = balance.cash + total_valuation

profit = total_valuation - total_investment
profit_rate = (profit / total_investment * 100) if total_investment > 0 else 0

print(f"총자산: {total_assets:,}원")
print(f"수익: {profit:,}원 ({profit_rate:.2f}%)")
```

---

## 에러 처리

### Q14: 연결이 자주 끊깁니다.

A: 재연결 로직을 추가하세요:

```python
from pykis.utils.retry import with_retry
from pykis.exceptions import KisConnectionError

@with_retry(max_retries=5, initial_delay=1.0)
def fetch_with_retry(symbol):
    try:
        return kis.stock(symbol).quote()
    except KisConnectionError as e:
        print(f"연결 실패: {e}")
        raise  # 재시도

try:
    quote = fetch_with_retry("005930")
except Exception as e:
    print(f"최종 실패: {e}")
```

### Q15: "MarketNotOpenedError" 에러가 발생합니다.

A: 주식 시장이 닫혀있을 때 발생합니다. 장 시간을 확인하세요:

```python
from pykis import PyKis

kis = PyKis(...)

# 장 시간 확인
hours = kis.stock("005930").trading_hours()

if hours.is_open_now:
    quote = kis.stock("005930").quote()
else:
    print(f"폐장 중. 다음 개장: {hours.next_open_time}")
```

---

## 고급 사용

### Q16: 데이터를 분석하기 위해 Pandas로 변환하려면?

A: 다음과 같이 변환할 수 있습니다:

```python
import pandas as pd
from pykis import PyKis

kis = PyKis(...)

# 차트 데이터를 DataFrame으로
charts = kis.stock("005930").chart("D")  # 일봉
df = pd.DataFrame([
    {
        "date": chart.date,
        "open": chart.open,
        "high": chart.high,
        "low": chart.low,
        "close": chart.close,
        "volume": chart.volume,
    }
    for chart in charts
])

# 분석
print(df.describe())
print(f"평균: {df['close'].mean()}")
print(f"표준편차: {df['close'].std()}")
```

### Q17: 매매 신호를 구현하려면?

A: 이동평균 교차 전략 예제:

```python
import pandas as pd
from pykis import PyKis

kis = PyKis(...)

# 데이터 준비
charts = kis.stock("005930").chart("D")
df = pd.DataFrame([...])  # 위 예제 참고

# 이동평균 계산
df['MA20'] = df['close'].rolling(20).mean()
df['MA60'] = df['close'].rolling(60).mean()

# 신호 생성
df['signal'] = 0
df.loc[df['MA20'] > df['MA60'], 'signal'] = 1  # 상향 신호
df.loc[df['MA20'] < df['MA60'], 'signal'] = -1  # 하향 신호

# 거래
latest = df.iloc[-1]
if latest['signal'] == 1 and df.iloc[-2]['signal'] != 1:
    print("매수 신호 발생!")
    kis.stock("005930").buy(price=latest['close'], qty=10)
```

### Q18: 로그 레벨을 조절하려면?

A: 다음과 같이 조절할 수 있습니다:

```python
from pykis import setLevel
from pykis.logging import enable_json_logging

# 로그 레벨 설정
setLevel("DEBUG")  # 상세 로그
setLevel("INFO")   # 기본 로그 (기본값)
setLevel("WARNING") # 경고와 에러만

# JSON 로깅 활성화 (프로덕션)
enable_json_logging()

# 이후 로그는 JSON 형식으로 출력
kis = PyKis(...)
# ... 코드 실행 ...
```

---

## 기여 및 지원

### Q19: 버그를 발견했습니다. 어떻게 보고하나요?

A: 다음 단계를 따르세요:

1. [GitHub Issues](https://github.com/QuantumOmega/python-kis/issues) 방문
2. "New Issue" 클릭
3. 버그 설명 (제목, 상세 내용, 재현 방법, 환경 정보 포함)
4. 제출

**좋은 버그 리포트 예제:**
```
Title: 401 에러 발생 시 재시도 불가능

Description:
...상세 설명...

Environment:
- OS: Windows 11
- Python: 3.11.9
- pykis: 2.1.7

Steps to reproduce:
1. 잘못된 AppKey로 인증 시도
2. 401 에러 발생
3. 재시도 시도 (with_retry 데코레이터 사용)
...

Expected behavior:
자동 재시도되어야 함

Actual behavior:
즉시 실패
```

### Q20: 기여하고 싶습니다. 어떻게 시작하나요?

A: 다음 단계를 따르세요:

1. [CONTRIBUTING.md](../CONTRIBUTING.md) 읽기
2. 리포지토리 Fork
3. Feature 브랜치 생성: `git checkout -b feature/my-feature`
4. 변경사항 commit: `git commit -am 'Add new feature'`
5. 브랜치 push: `git push origin feature/my-feature`
6. Pull Request 생성

**기여 가이드라인:**
- PEP 8 준수
- 테스트 추가 (커버리지 90%+ 유지)
- 문서 업데이트
- Commit 메시지는 명확하게

---

## 문제 해결

### Q21: Windows에서 "인코딩" 에러가 발생합니다.

A: 다음과 같이 해결하세요:

```python
# Python 파일 상단에 추가
# -*- coding: utf-8 -*-

import sys
import os

# 또는 환경 변수 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 파일 읽을 때 명시적으로 인코딩 지정
with open('config.yaml', 'r', encoding='utf-8') as f:
    ...
```

### Q22: Docker에서 실행할 수 있나요?

A: 네, Dockerfile 예제:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install -r requirements.txt

# 코드 복사
COPY . .

# 실행
CMD ["python", "main.py"]
```

**requirements.txt:**
```
pykis>=2.1.0
pyyaml>=6.0
python-dotenv>=1.2.0
```

### Q23: 성능을 최적화하려면?

A: 다음 팁을 참고하세요:

1. **배치 요청 사용** (가능하면)
```python
# 비효율적
for symbol in symbols:
    quote = kis.stock(symbol).quote()

# 효율적 (있으면)
quotes = kis.stocks(symbols).quotes()
```

2. **비동기 처리 사용**
```python
import asyncio

async def fetch_all():
    tasks = [kis.stock(s).quote_async() for s in symbols]
    return await asyncio.gather(*tasks)

results = asyncio.run(fetch_all())
```

3. **로깅 레벨 조정**
```python
setLevel("WARNING")  # 불필요한 로그 제거
```

4. **캐싱 활용** (응용 프로그램 레벨)
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_quote(symbol):
    return kis.stock(symbol).quote()
```

---

## 추가 리소스

- 📚 [공식 문서](https://github.com/QuantumOmega/python-kis)
- 💬 [GitHub Discussions](https://github.com/QuantumOmega/python-kis/discussions)
- 🐛 [Bug Reports](https://github.com/QuantumOmega/python-kis/issues)
- 📖 [Tutorial](../QUICKSTART.md)
- 🔗 [한국투자증권 API](https://www.truefriend.com)

---

**마지막 업데이트**: 2025-12-20
**문의**: [GitHub Discussions](https://github.com/QuantumOmega/python-kis/discussions) 또는 [Issues](https://github.com/QuantumOmega/python-kis/issues)
"""
