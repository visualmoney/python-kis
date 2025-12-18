"""기본 주문 예제 (안전 장치 포함).

- 기본값은 virtual=False로 가정하지 않습니다. config.yaml의 virtual 값이
  False이면 실제 주문이 발생할 수 있으므로, 환경 변수 ALLOW_LIVE_TRADES=1을
  설정하지 않으면 실행이 중단됩니다.
- 실제 주문 전 반드시 모의투자 계정으로 검증하세요.
"""
import os
import yaml
from pykis import PyKis


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> None:
    cfg = load_config()

    allow_live = os.environ.get("ALLOW_LIVE_TRADES") == "1"
    is_virtual = cfg.get("virtual", False)

    if not is_virtual and not allow_live:
        raise SystemExit(
            "config.yaml이 실계좌로 설정되어 있습니다. 모의투자를 사용하거나 "
            "ALLOW_LIVE_TRADES=1 환경 변수를 설정한 뒤 실행하세요."
        )

    kis = PyKis(
        id=cfg["id"],
        account=cfg["account"],
        appkey=cfg["appkey"],
        secretkey=cfg["secretkey"],
        virtual=is_virtual,
    )

    stock = kis.stock("005930")  # 삼성전자

    # 예시: 시장가 매수 1주 (실계좌/모의투자 설정에 따라 실행)
    order = stock.buy(qty=1)
    print(order)


if __name__ == "__main__":
    main()
