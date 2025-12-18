# SimpleKIS: 완벽한 초보자 인터페이스

일반적인 `PyKis` 사용법 외에, 더 간단한 인터페이스를 원한다면 **`SimpleKIS`** 파사드를 사용하세요.
`SimpleKIS`는 Protocol과 Mixin 없이 직관적인 메서드만 제공합니다.

## 1. 기본 사용법

### 1.1 방법 1: create_client 헬퍼 사용 (권장)

```python
from pykis import create_client
from pykis.simple import SimpleKIS

# config.yaml에서 자동 로드하여 클라이언트 생성
kis = create_client("config.yaml")
simple = SimpleKIS(kis)

# 사용
price = simple.get_price("005930")
print(f"삼성전자: {price.price:,}원")
```

### 1.2 방법 2: 직접 생성

```python
from pykis import PyKis, KisAuth
from pykis.simple import SimpleKIS

# 인증 정보 직접 지정
auth = KisAuth(
    id="YOUR_ID",
    appkey="YOUR_APPKEY",
    secretkey="YOUR_SECRET",
    account="00000000-01",
    virtual=True  # 모의투자 모드
)

# PyKis 생성 (virtual_auth 사용)
kis = PyKis(None, auth)
simple = SimpleKIS(kis)
```

### 1.3 방법 3: 대화형 설정 저장 후 사용

```python
from pykis.helpers import save_config_interactive, create_client
from pykis.simple import SimpleKIS

# 처음 한 번만: 대화형으로 설정 저장
# (입력 숨겨짐 + 마스킹 + 확인 단계)
config = save_config_interactive("config.yaml")

# 이후 사용
kis = create_client("config.yaml")
simple = SimpleKIS(kis)
```

---

## 2. 주요 메서드

### 2.1 시세 조회

```python
# 단일 종목
price = simple.get_price("005930")  # 삼성전자
print(f"종목: {price.name}")
print(f"현재가: {price.price:,}원")
print(f"등락률: {price.change_rate}%")
print(f"거래량: {price.volume:,}")

# 여러 종목
symbols = ["005930", "000660", "051910"]
prices = {sym: simple.get_price(sym) for sym in symbols}
for sym, price in prices.items():
    print(f"{sym}: {price.price:,}원")
```

### 2.2 잔고 조회

```python
balance = simple.get_balance()
print(f"예수금: {balance.deposits:,}원")
print(f"총자산: {balance.total_assets:,}원")
print(f"평가손익: {balance.revenue:,}원")
print(f"수익률: {balance.revenue_rate}%")
```

### 2.3 주문

```python
# 매수
order = simple.place_order(
    symbol="005930",
    side="buy",
    qty=1,
    price=65000
)
print(f"주문 번호: {order.order_id}")
print(f"상태: {order.status}")

# 매도
order = simple.place_order(
    symbol="005930",
    side="sell",
    qty=1,
    price=70000
)

# 시장가 주문 (price 생략)
order = simple.place_order(
    symbol="005930",
    side="buy",
    qty=1
)
```

### 2.4 주문 취소

```python
# 주문 취소
success = simple.cancel_order(order_id="12345678")
if success:
    print("주문이 취소되었습니다.")
else:
    print("주문 취소에 실패했습니다.")
```

---

## 3. 헬퍼 함수

### 3.1 설정 로드

```python
from pykis.helpers import load_config

# YAML에서 설정 로드
config = load_config("config.yaml")
print(config)
# {'id': '...', 'account': '...', 'appkey': '...', 'secretkey': '...', 'virtual': True}
```

### 3.2 대화형 설정 저장 (보안)

```python
from pykis.helpers import save_config_interactive

# 대화형으로 설정 저장
# - 비밀키는 getpass로 입력 숨겨짐
# - 저장 전 마스킹된 미리보기 제공
# - 사용자 확인 필수

config = save_config_interactive("config.yaml")
```

**입력 예시:**
```
HTS id: my_id
Account (XXXXXXXX-XX): 12345678-01
AppKey: my_appkey
SecretKey (input hidden): (숨겨진 입력)
Virtual (y/n): y

About to write the following config to: config.yaml
  id: my_id
  account: 12345678-01
  appkey: my_appkey
  secretkey: m...  (마스킹)
  virtual: True

Write config file? (y/N): y
```

**환경변수로 확인 단계 건너뛰기 (CI/CD용):**
```bash
export PYKIS_CONFIRM_SKIP=1
python your_script.py
```

### 3.3 자동 클라이언트 생성

```python
from pykis.helpers import create_client
from pykis.simple import SimpleKIS

# 자동으로 PyKis 생성 (virtual 설정 포함)
kis = create_client("config.yaml", keep_token=True)
simple = SimpleKIS(kis)
```

---

## 4. SimpleKIS vs PyKis 비교

| 기능 | SimpleKIS | PyKis |
|------|-----------|-------|
| **학습곡선** | ⭐⭐⭐⭐⭐ 초보자 | ⭐⭐⭐ 중급+ |
| **메서드 개수** | 4개 | 150+개 |
| **Protocol/Mixin** | 불필요 | 필수 (Scope + Adapter) |
| **WebSocket** | ❌ 미지원 | ✅ 지원 |
| **커스텀 확장** | 제한적 | 매우 강력 |
| **차트 데이터** | ❌ 미지원 | ✅ 지원 |
| **호가 정보** | ❌ 미지원 | ✅ 지원 |

**언제 SimpleKIS를 쓸까?**
- 시세, 잔고, 간단한 주문만 필요할 때
- API를 빠르게 학습하고 싶을 때
- 프로토타이핑이나 스크립트 작업

**언제 PyKis를 쓸까?**
- 웹소켓 실시간 데이터가 필요할 때
- 차트, 호가, 복잡한 분석이 필요할 때
- 고급 거래 전략을 구현할 때

---

## 5. 실제 예제

### 5.1 여러 종목 모니터링

```python
from pykis import create_client
from pykis.simple import SimpleKIS
import time

kis = create_client("config.yaml")
simple = SimpleKIS(kis)

symbols = ["005930", "000660", "051910"]

while True:
    print("\n=== 시장 현황 ===")
    for sym in symbols:
        price = simple.get_price(sym)
        arrow = "📈" if price.change_rate > 0 else "📉"
        print(f"{arrow} {sym}: {price.price:,}원 ({price.change_rate:+.2f}%)")
    
    balance = simple.get_balance()
    print(f"\n💰 총자산: {balance.total_assets:,}원")
    
    time.sleep(60)  # 1분마다 갱신
```

### 5.2 자동 거래

```python
from pykis import create_client
from pykis.simple import SimpleKIS

kis = create_client("config.yaml")
simple = SimpleKIS(kis)

# 삼성전자가 65,000원 이하면 매수
price = simple.get_price("005930")
if price.price <= 65000:
    order = simple.place_order(
        symbol="005930",
        side="buy",
        qty=1,
        price=65000
    )
    print(f"매수 주문 완료: {order.order_id}")
else:
    print(f"현재 가격({price.price:,}원)이 목표가(65,000원) 이상입니다.")
```

### 5.3 잔고 확인 및 거래 여부 결정

```python
from pykis import create_client
from pykis.simple import SimpleKIS

kis = create_client("config.yaml")
simple = SimpleKIS(kis)

balance = simple.get_balance()
print(f"예수금: {balance.deposits:,}원")
print(f"총자산: {balance.total_assets:,}원")

# 예수금이 100만원 이상일 때만 매수
if balance.deposits >= 1_000_000:
    order = simple.place_order(
        symbol="005930",
        side="buy",
        qty=1,
        price=65000
    )
    print(f"주문 완료: {order.order_id}")
else:
    print(f"예수금 부족({balance.deposits:,}원 < 1,000,000원)")
```

---

## 6. 주의사항 ⚠️

### 6.1 실계좌 주문

```python
# virtual=True (모의투자)
auth = KisAuth(..., virtual=True)
kis = PyKis(None, auth)
simple = SimpleKIS(kis)
order = simple.place_order(...)  # 모의투자에서만 실행

# virtual=False (실계좌) - 실제 주문!
auth = KisAuth(..., virtual=False)
kis = PyKis(auth)
simple = SimpleKIS(kis)
order = simple.place_order(...)  # 💰 실제 주문 발생!
```

**테스트 프로세스:**
1. `virtual=True`로 모의투자에서 전부 검증
2. `ALLOW_LIVE_TRADES=1` 환경변수 설정 필수
3. 실계좌에서 소액으로 테스트
4. 정상 작동 확인 후 본격 사용

### 6.2 보안 (설정 저장)

```python
# ❌ 나쁜 예: 코드에 직접 작성
from pykis import KisAuth
auth = KisAuth(
    id="my_id",
    appkey="my_appkey",
    secretkey="my_secret",  # 😱 코드에 노출!
    account="12345678-01"
)

# ✅ 좋은 예: 파일에서 로드
from pykis.helpers import create_client
kis = create_client("config.yaml")  # 설정 외부화

# ✅ 더 나은 예: 대화형 저장 (보안 강화)
from pykis.helpers import save_config_interactive
config = save_config_interactive("config.yaml")
# - getpass로 비밀키 숨김
# - 마스킹된 미리보기
# - 사용자 확인
```

### 6.3 에러 처리

```python
from pykis import create_client
from pykis.simple import SimpleKIS

try:
    kis = create_client("config.yaml")
    simple = SimpleKIS(kis)
    price = simple.get_price("005930")
    print(f"현재가: {price.price:,}원")
except FileNotFoundError:
    print("❌ config.yaml이 없습니다.")
except Exception as e:
    print(f"❌ 오류: {e}")
```

---

## 7. 성능 팁

```python
# ⏱️ 여러 종목을 순차적으로 조회 (느림)
prices = []
for sym in ["005930", "000660", "051910"]:
    price = simple.get_price(sym)
    prices.append(price)

# ⚡ 병렬 요청 (빠름)
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=3) as executor:
    results = executor.map(simple.get_price, ["005930", "000660", "051910"])
    prices = list(results)
```

---

## 8. 다음 단계

- **PyKis로 업그레이드**: 웹소켓, 차트, 호가 등 고급 기능 학습
- **전략 개발**: 실제 거래 전략 구현 및 백테스팅
- **자동화**: 스케줄 기반 자동 거래 시스템 구축
- **모니터링**: 포트폴리오 성과 추적 및 리포팅

**예제:**
- `examples/01_basic/` - 기본 사용법
- `examples/02_intermediate/` - 중급 예제 (예정)
- `examples/03_advanced/` - 고급 예제 (예정)
