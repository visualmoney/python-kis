# QUICKSTART

1. 설치

```bash
pip install python-kis
```

2. 인증 정보 준비 (권장: 외부 파일 사용, 리포지토리에 커밋 금지)

`config.yaml` 예시:

```yaml
id: "YOUR_HTS_ID"
account: "00000000-01"
appkey: "YOUR_APPKEY"
secretkey: "YOUR_SECRET"
virtual: false
```

3. 코드 예시 (config.yaml 사용)

```python
import yaml
from pykis import PyKis

with open("config.yaml", "r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

kis = PyKis(id=cfg["id"], account=cfg["account"], appkey=cfg["appkey"], secretkey=cfg["secretkey"])
print(kis.stock("005930").quote())
```

4. 테스트 팁

- 테스트에서는 `tmp_path`에 임시 `config.yaml`을 생성하거나 `monkeypatch.setenv`를 사용하세요.
