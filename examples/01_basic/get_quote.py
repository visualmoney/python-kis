"""기본 시세 조회 예제.

이 예제는 config.yaml에서 인증 정보를 로드한 뒤
삼성전자(005930) 시세를 조회해 출력합니다.
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
    quote = stock.quote()
    print(quote)


if __name__ == "__main__":
    main()
