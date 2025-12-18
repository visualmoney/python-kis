"""실시간 체결가 구독 예제.

- 삼성전자(005930) 실시간 체결가를 구독합니다.
- 종료하려면 Enter를 누르세요.
"""
import yaml
from pykis import PyKis


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> None:
    cfg = load_config()

    kis = PyKis(
        id=cfg["id"],
        account=cfg["account"],
        appkey=cfg["appkey"],
        secretkey=cfg["secretkey"],
        virtual=cfg.get("virtual", False),
    )

    stock = kis.stock("005930")  # 삼성전자

    def on_price(sender, e):
        print(e.response)

    ticket = stock.on("price", on_price)
    try:
        input("Press Enter to stop streaming...\n")
    finally:
        ticket.unsubscribe()


if __name__ == "__main__":
    main()
