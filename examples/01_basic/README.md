# Basic Examples

이 폴더는 빠른 시작을 위한 최소 예제들을 제공합니다. 모두 `config.yaml` (루트)에서 인증 정보를 로드합니다. 민감정보가 있으니 리포지토리에 커밋하지 마세요.

## 준비
1. 루트에 `config.yaml` 생성 (QUICKSTART.md 참고)
2. 가급적 `virtual: true`로 모의투자 계정을 사용
3. 실계좌 주문 시 환경 변수 `ALLOW_LIVE_TRADES=1`을 설정해야 예제가 실행됩니다.

## 예제 목록
- `hello_world.py` — 기본 초기화 및 `stock("005930").quote()` 출력
- `get_quote.py` — 시세 조회 예제 (삼성전자)
- `get_balance.py` — 잔고 조회 예제
- `place_order.py` — 시장가 매수 예제 (안전 장치 포함)
- `realtime_price.py` — 실시간 체결가 구독 예제

## 실행 방법
```bash
python examples/01_basic/hello_world.py
python examples/01_basic/get_quote.py
python examples/01_basic/get_balance.py
python examples/01_basic/place_order.py   # 모의투자 권장
python examples/01_basic/realtime_price.py
```

## 주의사항
- 실계좌로 주문하려면 `ALLOW_LIVE_TRADES=1`을 명시적으로 설정하세요.
- `config.yaml`와 토큰/로그는 절대 커밋하지 마세요.
- 실시간 예제는 종료 시 Enter를 눌러 구독을 해제하세요.
