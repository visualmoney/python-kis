import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

from pykis.api.account import daily_order as dord
from pykis.client.page import KisPage


def test_domestic_exchange_code_map_basic():
    # verify some known mappings
    assert dord.DOMESTIC_EXCHANGE_CODE_MAP["01"][0] == "KR"
    assert dord.DOMESTIC_EXCHANGE_CODE_MAP["51"][0] == "HK"
    assert dord.DOMESTIC_EXCHANGE_CODE_MAP["61"][2] == "before"


def test_kis_daily_order_base_amounts_and_qtys():
    inst = object.__new__(dord.KisDailyOrderBase)
    inst.unit_price = Decimal("10")
    inst.price = Decimal("9")
    inst.quantity = Decimal("5")
    inst.executed_quantity = Decimal("3")
    inst.pending_quantity = Decimal("2")

    # order_price proxies unit_price
    assert inst.order_price == Decimal("10")
    # qty proxies quantity
    assert inst.qty == Decimal("5")
    # executed_qty proxies executed_quantity
    assert inst.executed_qty == Decimal("3")
    # executed_amount uses price (not unit_price)
    assert inst.executed_amount == Decimal("27")
    # pending_qty proxies pending_quantity
    assert inst.pending_qty == Decimal("2")


def test__domestic_daily_orders_calls_fetch_and_returns_result():
    # Create a fake 'self' with a fetch that returns a simple object
    calls = []

    class FakeSelf:
        def __init__(self):
            self.virtual = False

        def fetch(self, *args, **kwargs):
            calls.append((args, kwargs))
            # Return an object that mimics the API response used by the function
            return SimpleNamespace(is_last=True, orders=["A"], next_page=None)

    fake = FakeSelf()
    start = date.today() - timedelta(days=1)
    end = date.today()

    res = dord._domestic_daily_orders(fake, account="12345678", start=start, end=end)
    assert res.orders == ["A"]
    # verify fetch was called once and with expected kwargs including form
    assert len(calls) == 1
    _, kw = calls[0]
    assert "form" in kw


def test_domestic_daily_orders_swapped_dates_and_page_to():
    class FakeSelf:
        def __init__(self):
            self.virtual = False

        def fetch(self, *args, **kwargs):
            return SimpleNamespace(is_last=True, orders=[], next_page=None)

    fake = FakeSelf()
    # pass start > end and ensure no exception (function swaps)
    start = date(2020, 5, 1)
    end = date(2020, 1, 1)
    res = dord._domestic_daily_orders(fake, account="12345678", start=start, end=end)
    assert hasattr(res, "orders")


def test_kis_integration_daily_orders_merges_and_sorts():
    # create two small KisDailyOrders-like objects
    o1 = SimpleNamespace(orders=[SimpleNamespace(time_kst=datetime(2021, 1, 2)), SimpleNamespace(time_kst=datetime(2021, 1, 1))])
    o2 = SimpleNamespace(orders=[SimpleNamespace(time_kst=datetime(2021, 1, 3))])

    kd = dord.KisIntegrationDailyOrders(None, "ACC", o1, o2)
    # merged and sorted in descending order by time_kst
    times = [o.time_kst for o in kd.orders]
    assert times == sorted(times, reverse=True)
