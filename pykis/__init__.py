from pykis.__env__ import (
    __author__,
    __author_email__,
    __license__,
    __package_name__,
    __url__,
    __version__,
)
from pykis.exceptions import *
from pykis.kis import PyKis

# 공개 타입은 `pykis.public_types`에서 재export
from pykis.public_types import (
    Quote,
    Balance,
    Order,
    Chart,
    Orderbook,
    MarketInfo,
    TradingHours,
)

# 핵심 인증/클래스
from pykis.client.auth import KisAuth

try:
    # 초보자용 유틸(선택적)
    from pykis.simple import SimpleKIS
    from pykis.helpers import create_client, save_config_interactive
except Exception:
    SimpleKIS = None
    create_client = None
    save_config_interactive = None

__all__ = [
    # 핵심
    "PyKis",
    "KisAuth",

    # 공개 타입
    "Quote",
    "Balance",
    "Order",
    "Chart",
    "Orderbook",
    "MarketInfo",
    "TradingHours",

    # 초보자 도구
    "SimpleKIS",
    "create_client",
    "save_config_interactive",
]

# 하위 호환성: deprecated된 루트 import를 types 모듈로 위임하고 경고를 보냄
import warnings
from importlib import import_module
from typing import Any

_DEPRECATED_SOURCE = "pykis.types"

def __getattr__(name: str) -> Any:
    # Always warn about deprecated root-level imports so callers see a clear
    # deprecation notice even if the types module cannot be imported.
    warnings.warn(
        f"from pykis import {name} is deprecated; use 'from pykis.types import {name}' instead. This alias will be removed in a future major release.",
        DeprecationWarning,
        stacklevel=2,
    )

    try:
        module = import_module(_DEPRECATED_SOURCE)
    except Exception:
        raise AttributeError(f"module 'pykis' has no attribute '{name}'")

    if hasattr(module, name):
        return getattr(module, name)

    raise AttributeError(f"module 'pykis' has no attribute '{name}'")
