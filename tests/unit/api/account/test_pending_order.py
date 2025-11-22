from datetime import datetime, timedelta
import types

import pytest

from pykis.api.account import pending_order as po


def make_o(symbol, number, when):
    o = types.SimpleNamespace()
    o.symbol = symbol
    o.order_number = types.SimpleNamespace(branch="000", number=number)
    o.time_kst = when
    return o


def test_kissimplependingorders_indexing_and_order():
    now = datetime.utcnow()
    o1 = make_o("AAA", "1", now)
    o2 = make_o("BBB", "2", now - timedelta(days=1))

    coll = po.KisSimplePendingOrders(account_number="acct", orders=[o1, o2])

    # list is sorted reverse by time_kst in constructor
    assert coll.orders[0].time_kst >= coll.orders[1].time_kst

    assert coll[0] is coll.orders[0]
    assert coll["BBB"].symbol == "BBB"

    with pytest.raises(IndexError):
        _ = coll[999]

    assert coll.order("AAA") is not None
    assert coll.order("NOPE") is None

    assert len(coll) == 2
    assert list(iter(coll)) == coll.orders


def test_integration_pending_orders_merges_and_sorts():
    now = datetime.utcnow()
    a1 = make_o("A", "1", now)
    b1 = make_o("B", "2", now - timedelta(hours=1))
    part1 = types.SimpleNamespace(orders=[b1])
    part2 = types.SimpleNamespace(orders=[a1])

    integ = po.KisIntegrationPendingOrders(object(), "acct", part1, part2)

    # merged and sorted reverse by time_kst
    assert len(integ.orders) == 2
    assert integ.orders[0].time_kst >= integ.orders[1].time_kst


def test_domestic_pending_orders_raises_on_virtual():
    class FakeKis:
        def __init__(self):
            self.virtual = True

    with pytest.raises(NotImplementedError):
        po.domestic_pending_orders(FakeKis(), account="123")


def test_foreign_pending_orders_uses_foreign_map_and_calls_internal(monkeypatch):
    # ensure foreign_pending_orders calls _foreign_pending_orders for each mapped market
    called = []

    def fake_internal(kis, account, market=None, page=None, continuous=True):
        called.append(market)
        return types.SimpleNamespace(orders=[1])

    monkeypatch.setattr(po, "_foreign_pending_orders", fake_internal)

    res = po.foreign_pending_orders(object(), account="acct", country="US")
    # US maps to ['NASDAQ'] so our fake_internal should be called with that market
    assert called[0] == "NASDAQ"
    assert hasattr(res, "orders")
