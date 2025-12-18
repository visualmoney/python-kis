"""기본 잔고 조회 예제.

config.yaml의 인증 정보를 사용해 계좌 잔고를 조회합니다.
"""
import yaml
from pykis import PyKis, KisAuth


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> None:
    cfg = load_config()

    auth = KisAuth(
        id=cfg["id"],
        account=cfg["account"],
        appkey=cfg["appkey"],
        secretkey=cfg["secretkey"],
        virtual=cfg.get("virtual", False),
    )

    kis = PyKis(auth, keep_token=True)

    account = kis.account()
    balance = account.balance()
    print(balance)


if __name__ == "__main__":
    main()
