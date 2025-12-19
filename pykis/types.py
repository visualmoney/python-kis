"""
Python-KIS 내부 타입 및 Protocol 정의

⚠️ 주의: 이 모듈은 라이브러리 내부 및 고급 사용자용입니다.

==============================================================================
누가 사용해야 하나?
==============================================================================

1️⃣ **일반 사용자 (추천)**
   └─ from pykis import Quote, Balance, Order  (공개 타입 사용)
   └─ 설명서: docs/SIMPLEKIS_GUIDE.md, QUICKSTART.md

2️⃣ **Type Hint를 작성하는 개발자**
   ├─ from pykis import Quote, Balance, Order  (공개 타입)
   └─ Type Hint 작성 가능

3️⃣ **고급 사용자 / 기여자 (직접 import)**
   ├─ from pykis.types import KisObjectProtocol  (Protocol)
   ├─ from pykis.adapter.* import * (Adapter/Mixin)
   └─ docs/architecture/ARCHITECTURE.md 문서 정독 필수

==============================================================================
내용 구성
==============================================================================

이 모듈은 다음을 포함합니다:

### Adapter/Mixin 클래스
- KisQuotableAccount: 시세 조회 기능 추가
- KisOrderableAccount: 주문 기능 추가
- KisOrderableAccountProduct: 상품별 주문 기능
- KisRealtimeOrderableAccount: WebSocket 기반 실시간 주문
- KisQuotableProduct, KisWebsocketQuotableProduct: 종목별 시세 기능

### API 응답 타입
- KisBalance, KisOrder: 계좌 잔고/주문 정보
- KisChart, KisOrderbook: 차트, 호가 정보
- KisQuote, KisTradingHours: 시세, 장시간 정보
- KisRealtimePrice, KisRealtimeExecution: 실시간 시세, 체결 정보

### Protocol 인터페이스
- KisAccountProtocol: 계좌 관련 인터페이스
- KisProductProtocol: 종목 관련 인터페이스
- KisMarketProtocol: 시장 관련 인터페이스
- KisObjectProtocol: 기본 API 객체 인터페이스

### 이벤트 및 핸들러
- KisEventHandler: 이벤트 핸들러
- KisEventFilter, KisEventCallback: 이벤트 필터/콜백
- KisEventTicket: 이벤트 구독 티켓

### 클라이언트 기능
- KisAuth: 인증 정보
- KisWebsocketClient: WebSocket 연결
- KisPage: 페이지네이션

==============================================================================
버전 정책
==============================================================================

| 버전 | 상태 | 설명 |
|------|------|------|
| v2.2.0~v2.9.x | ✅ 활성 | 모든 항목 유지 (import 가능) |
| v3.0.0+ | ❌ 제거 | 직접 import 불가 (내부용으로 변경) |

마이그레이션 가이드:
- 현재(v2.2.0): 모든 기존 코드 계속 동작
- v2.3.0~v2.9.0: DeprecationWarning 표시하지만 동작
- v3.0.0: 기존 경로 제거, 새로운 경로 사용 필수

==============================================================================
사용 예제
==============================================================================

### ❌ 나쁜 예 (권장하지 않음)

```python
# 일반 사용자가 직접 import (복잡함)
from pykis.types import KisQuotableAccount, KisOrderableAccount
```

### ✅ 좋은 예 (권장)

```python
# 1. 공개 타입 사용
from pykis import Quote, Balance, Order

def analyze_quote(quote: Quote) -> None:
    print(f"가격: {quote.price}원")

# 2. SimpleKIS 파사드 사용
from pykis import create_client
from pykis.simple import SimpleKIS

kis = create_client("config.yaml")
simple = SimpleKIS(kis)
price = simple.get_price("005930")

# 3. 고급: PyKis 직접 사용 (필요시)
from pykis import PyKis

kis = PyKis(auth)
quote = kis.stock("005930").quote()
```

### 🔬 고급 사용 (기여자용)

```python
# Protocol을 활용한 커스텀 구현
from pykis.types import KisObjectProtocol

class MyCustomObject(KisObjectProtocol):
    def __init__(self, kis):
        self.kis = kis
    
    def custom_method(self):
        # 내부 API 활용
        return self.kis.fetch(...)
```

==============================================================================
"""

from pykis.adapter.account.balance import KisQuotableAccount
from pykis.adapter.account.order import KisOrderableAccount
from pykis.adapter.account_product.order import KisOrderableAccountProduct
from pykis.adapter.account_product.order_modify import (
    KisCancelableOrder,
    KisModifyableOrder,
    KisOrderableOrder,
)
from pykis.adapter.product.quote import KisQuotableProduct
from pykis.adapter.websocket.execution import KisRealtimeOrderableAccount
from pykis.adapter.websocket.price import KisWebsocketQuotableProduct
from pykis.api.account.balance import KisBalance, KisBalanceStock, KisDeposit
from pykis.api.account.daily_order import KisDailyOrder, KisDailyOrders
from pykis.api.account.order import (
    IN_ORDER_QUANTITY,
    ORDER_CONDITION,
    ORDER_EXECUTION,
    ORDER_PRICE,
    ORDER_QUANTITY,
    ORDER_TYPE,
    KisOrder,
    KisOrderNumber,
    KisSimpleOrder,
    KisSimpleOrderNumber,
)
from pykis.api.account.order_profit import KisOrderProfit, KisOrderProfits
from pykis.api.account.orderable_amount import (
    KisOrderableAmount,
    KisOrderableAmountResponse,
)
from pykis.api.account.pending_order import KisPendingOrder, KisPendingOrders
from pykis.api.auth.token import KisAccessToken
from pykis.api.auth.websocket import KisWebsocketApprovalKey
from pykis.api.base.account import KisAccountProtocol
from pykis.api.base.account_product import KisAccountProductProtocol
from pykis.api.base.market import KisMarketProtocol
from pykis.api.base.product import KisProductProtocol
from pykis.api.stock.chart import KisChart, KisChartBar
from pykis.api.stock.info import (
    COUNTRY_TYPE,
    MARKET_INFO_TYPES,
    KisStockInfo,
    KisStockInfoResponse,
)
from pykis.api.stock.market import CURRENCY_TYPE, MARKET_TYPE, ExDateType
from pykis.api.stock.order_book import (
    KisOrderbook,
    KisOrderbookItem,
    KisOrderbookResponse,
)
from pykis.api.stock.quote import (
    STOCK_RISK_TYPE,
    STOCK_SIGN_TYPE,
    KisIndicator,
    KisQuote,
    KisQuoteResponse,
)
from pykis.api.stock.trading_hours import KisTradingHours
from pykis.api.websocket.order_book import KisRealtimeOrderbook
from pykis.api.websocket.order_execution import KisRealtimeExecution
from pykis.api.websocket.price import KisRealtimePrice
from pykis.client.account import KisAccountNumber
from pykis.client.appkey import KisKey
from pykis.client.auth import KisAuth
from pykis.client.cache import KisCacheStorage
from pykis.client.form import KisForm
from pykis.client.messaging import (
    KisWebsocketEncryptionKey,
    KisWebsocketForm,
    KisWebsocketRequest,
    KisWebsocketTR,
)
from pykis.client.object import KisObjectProtocol
from pykis.client.page import KisPage, KisPageStatus
from pykis.client.websocket import KisWebsocketClient
from pykis.event.filters.order import KisOrderNumberEventFilter
from pykis.event.filters.product import KisProductEventFilter
from pykis.event.filters.subscription import KisSubscriptionEventFilter
from pykis.event.handler import (
    EventCallback,
    KisEventArgs,
    KisEventCallback,
    KisEventFilter,
    KisEventHandler,
    KisEventTicket,
    KisLambdaEventCallback,
    KisLambdaEventFilter,
    KisMultiEventFilter,
)
from pykis.event.subscription import (
    KisSubscribedEventArgs,
    KisSubscriptionEventArgs,
    KisUnsubscribedEventArgs,
)
from pykis.kis import PyKis
from pykis.responses.response import (
    KisAPIResponse,
    KisPaginationAPIResponse,
    KisPaginationAPIResponseProtocol,
    KisResponse,
    KisResponseProtocol,
)
from pykis.responses.websocket import KisWebsocketResponse, KisWebsocketResponseProtocol
from pykis.scope.account import KisAccount, KisAccountScope
from pykis.scope.base import KisScope, KisScopeBase
from pykis.scope.stock import KisStock, KisStockScope
from pykis.utils.timex import TIMEX_TYPE

__all__ = [
    ################################
    ##            Types           ##
    ################################
    "TIMEX_TYPE",
    "COUNTRY_TYPE",
    "MARKET_TYPE",
    "CURRENCY_TYPE",
    "MARKET_INFO_TYPES",
    "ExDateType",
    "STOCK_SIGN_TYPE",
    "STOCK_RISK_TYPE",
    "ORDER_TYPE",
    "ORDER_PRICE",
    "ORDER_EXECUTION",
    "ORDER_CONDITION",
    "ORDER_QUANTITY",
    "IN_ORDER_QUANTITY",
    ################################
    ##             API            ##
    ################################
    "PyKis",
    "KisAccessToken",
    "KisAccountNumber",
    "KisKey",
    "KisAuth",
    "KisCacheStorage",
    "KisForm",
    "KisPage",
    "KisPageStatus",
    ################################
    ##          Websocket         ##
    ################################
    "KisWebsocketApprovalKey",
    "KisWebsocketForm",
    "KisWebsocketRequest",
    "KisWebsocketTR",
    "KisWebsocketEncryptionKey",
    "KisWebsocketClient",
    ################################
    ##            Events          ##
    ################################
    "EventCallback",
    "KisEventArgs",
    "KisEventCallback",
    "KisEventFilter",
    "KisEventHandler",
    "KisEventTicket",
    "KisLambdaEventCallback",
    "KisLambdaEventFilter",
    "KisMultiEventFilter",
    "KisSubscribedEventArgs",
    "KisUnsubscribedEventArgs",
    "KisSubscriptionEventArgs",
    ################################
    ##        Event Filters       ##
    ################################
    "KisProductEventFilter",
    "KisOrderNumberEventFilter",
    "KisSubscriptionEventFilter",
    ################################
    ##            Scope           ##
    ################################
    "KisScope",
    "KisScopeBase",
    "KisAccountScope",
    "KisAccount",
    "KisStock",
    "KisStockScope",
    ################################
    ##          Responses         ##
    ################################
    "KisAPIResponse",
    "KisResponse",
    "KisResponseProtocol",
    "KisPaginationAPIResponse",
    "KisPaginationAPIResponseProtocol",
    "KisWebsocketResponse",
    "KisWebsocketResponseProtocol",
    ################################
    ##          Protocols         ##
    ################################
    "KisObjectProtocol",
    "KisMarketProtocol",
    "KisProductProtocol",
    "KisAccountProtocol",
    "KisAccountProductProtocol",
    "KisStockInfo",
    "KisOrderbook",
    "KisOrderbookItem",
    "KisChartBar",
    "KisChart",
    "KisTradingHours",
    "KisIndicator",
    "KisQuote",
    "KisBalanceStock",
    "KisDeposit",
    "KisBalance",
    "KisDailyOrder",
    "KisDailyOrders",
    "KisOrderProfit",
    "KisOrderProfits",
    "KisOrderNumber",
    "KisOrder",
    "KisSimpleOrderNumber",
    "KisSimpleOrder",
    "KisOrderableAmount",
    "KisPendingOrder",
    "KisPendingOrders",
    "KisRealtimeOrderbook",
    "KisRealtimeExecution",
    "KisRealtimePrice",
    ################################
    ##           Adapters         ##
    ################################
    "KisQuotableAccount",
    "KisOrderableAccount",
    "KisOrderableAccountProduct",
    "KisQuotableProduct",
    "KisRealtimeOrderableAccount",
    "KisWebsocketQuotableProduct",
    "KisCancelableOrder",
    "KisModifyableOrder",
    "KisOrderableOrder",
    ################################
    ##        API Responses       ##
    ################################
    "KisStockInfoResponse",
    "KisOrderbookResponse",
    "KisQuoteResponse",
    "KisOrderableAmountResponse",
]
