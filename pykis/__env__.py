import sys
from importlib.metadata import version as _dist_version

APPKEY_LENGTH = 36
SECRETKEY_LENGTH = 180

REAL_DOMAIN = "https://openapi.koreainvestment.com:9443"
VIRTUAL_DOMAIN = "https://openapivts.koreainvestment.com:29443"

WEBSOCKET_REAL_DOMAIN = "ws://ops.koreainvestment.com:21000"
WEBSOCKET_VIRTUAL_DOMAIN = "ws://ops.koreainvestment.com:31000"

WEBSOCKET_MAX_SUBSCRIPTIONS = 40

REAL_API_REQUEST_PER_SECOND = 20 - 1
VIRTUAL_API_REQUEST_PER_SECOND = 2

TRACE_DETAIL_ERROR: bool = False
"""
경고: 해당 기능은 HTTPStatusCode 200이 아닌 경우. 상세한 요청, 응답을 출력합니다.

이로 인해 예외 메세지에서 앱 키가 노출될 수 있습니다.
"""

# 배포 메타데이터에서 버전 읽기 (poetry-dynamic-versioning 플러그인 주입)
try:
    __version__ = _dist_version("python-kis")
except Exception:
    # 소스 실행 환경에서 fallback (태그 없을 때)
    __version__ = "2.1.6+dev"

USER_AGENT = f"PyKis/{__version__}"

__package_name__ = "python-kis"
__author__ = "soju06"
__author_email__ = "qlskssk@gmail.com"
__url__ = "https://github.com/soju06/python-kis"
__license__ = "MIT"

if sys.version_info < (3, 10):
    raise RuntimeError(f"PyKis에는 Python 3.10 이상이 필요합니다. (Current: {sys.version})")

