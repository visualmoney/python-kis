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


def test_kis_pending_order_base_properties():
    """Test KisPendingOrderBase property aliases."""
    from decimal import Decimal
    
    order = types.SimpleNamespace(
        unit_price=Decimal("50000"),
        quantity=100,
        executed_quantity=60,
        orderable_quantity=40,
        price=Decimal("50000")
    )
    
    # Create instance
    pending_order = object.__new__(po.KisPendingOrderBase)
    pending_order.unit_price = order.unit_price
    pending_order.quantity = order.quantity
    pending_order.executed_quantity = order.executed_quantity
    pending_order.orderable_quantity = order.orderable_quantity
    pending_order.price = order.price
    
    # Test property aliases
    assert pending_order.order_price == Decimal("50000")
    assert pending_order.qty == 100
    assert pending_order.executed_qty == 60
    assert pending_order.orderable_qty == 40
    assert pending_order.pending_quantity == 40  # quantity - executed_quantity
    assert pending_order.pending_qty == 40
    assert pending_order.executed_amount == Decimal("3000000")  # 60 * 50000


def test_kis_pending_order_base_executed_amount_with_none_price():
    """Test executed_amount when price is None."""
    from decimal import Decimal
    
    pending_order = object.__new__(po.KisPendingOrderBase)
    pending_order.executed_quantity = 100
    pending_order.price = None
    
    assert pending_order.executed_amount == Decimal(0)


def test_kis_pending_order_base_pending_property():
    """Test pending property returns True."""
    pending_order = object.__new__(po.KisPendingOrderBase)
    assert pending_order.pending is True


def test_kis_pending_order_base_pending_order_property():
    """Test pending_order property returns self."""
    pending_order = object.__new__(po.KisPendingOrderBase)
    assert pending_order.pending_order is pending_order


def test_kis_pending_orders_base_getitem_by_index():
    """Test __getitem__ with integer index."""
    orders_list = [
        make_o("005930", "1", datetime.utcnow()),
        make_o("AAPL", "2", datetime.utcnow())
    ]
    
    pending_orders = object.__new__(po.KisPendingOrdersBase)
    pending_orders.orders = orders_list
    
    assert pending_orders[0].symbol == "005930"
    assert pending_orders[1].symbol == "AAPL"


def test_kis_pending_orders_base_getitem_by_symbol():
    """Test __getitem__ with symbol string."""
    orders_list = [
        make_o("005930", "1", datetime.utcnow()),
        make_o("AAPL", "2", datetime.utcnow())
    ]
    
    pending_orders = object.__new__(po.KisPendingOrdersBase)
    pending_orders.orders = orders_list
    
    assert pending_orders["005930"].order_number.number == "1"
    assert pending_orders["AAPL"].order_number.number == "2"


def test_kis_pending_orders_base_getitem_keyerror():
    """Test __getitem__ raises KeyError for non-existent key."""
    orders_list = [make_o("005930", "1", datetime.utcnow())]
    
    pending_orders = object.__new__(po.KisPendingOrdersBase)
    pending_orders.orders = orders_list
    
    with pytest.raises(KeyError):
        _ = pending_orders["NONEXISTENT"]


def test_kis_pending_orders_base_order_by_symbol():
    """Test order() method with symbol."""
    orders_list = [
        make_o("005930", "1", datetime.utcnow()),
        make_o("AAPL", "2", datetime.utcnow())
    ]
    
    pending_orders = object.__new__(po.KisPendingOrdersBase)
    pending_orders.orders = orders_list
    
    result = pending_orders.order("005930")
    assert result is not None
    assert result.order_number.number == "1"
    
    # Non-existent symbol returns None
    result = pending_orders.order("NONEXISTENT")
    assert result is None


def test_kis_pending_orders_base_len():
    """Test __len__ method."""
    orders_list = [
        make_o("005930", "1", datetime.utcnow()),
        make_o("AAPL", "2", datetime.utcnow()),
        make_o("MSFT", "3", datetime.utcnow())
    ]
    
    pending_orders = object.__new__(po.KisPendingOrdersBase)
    pending_orders.orders = orders_list
    
    assert len(pending_orders) == 3


def test_kis_pending_orders_base_iter():
    """Test __iter__ method."""
    orders_list = [
        make_o("005930", "1", datetime.utcnow()),
        make_o("AAPL", "2", datetime.utcnow())
    ]
    
    pending_orders = object.__new__(po.KisPendingOrdersBase)
    pending_orders.orders = orders_list
    
    symbols = [order.symbol for order in pending_orders]
    assert symbols == ["005930", "AAPL"]


def test_kis_pending_order_base_equality():
    """Test __eq__ method compares order_number."""
    order1 = object.__new__(po.KisPendingOrderBase)
    order1.order_number = types.SimpleNamespace(branch="000", number="123")
    
    order2 = object.__new__(po.KisPendingOrderBase)
    order2.order_number = types.SimpleNamespace(branch="000", number="123")
    
    # Should be equal if order_number is equal
    assert order1 == order1.order_number
    assert order1 == order2.order_number


def test_kis_pending_order_base_hash():
    """Test __hash__ method uses order_number."""
    # Create a hashable mock order number
    class MockOrderNumber:
        def __init__(self, branch, number):
            self.branch = branch
            self.number = number
        
        def __hash__(self):
            return hash((self.branch, self.number))
        
        def __eq__(self, other):
            return self.branch == other.branch and self.number == other.number
    
    order = object.__new__(po.KisPendingOrderBase)
    order.order_number = MockOrderNumber("000", "123")
    
    # Should be hashable
    assert isinstance(hash(order), int)
    assert hash(order) == hash(order.order_number)
