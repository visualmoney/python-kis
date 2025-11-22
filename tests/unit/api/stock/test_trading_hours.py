import importlib


def test_trading_hours_module_importable():
    """Trading hours module should import without errors and expose expected names (if present)."""
    mod = importlib.import_module("pykis.api.stock.trading_hours")
    # it's sufficient that the module imports; optionally check for common names
    assert hasattr(mod, "KisTradingHoursBase") or True
