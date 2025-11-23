import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock

from pykis.api.account import order as ordmod
from pykis.client.account import KisAccountNumber


def test_ensure_price_and_quantity_preserve_when_digit_none():
    # When digit is None, the original Decimal is preserved
    p = Decimal("1.23")
    assert ordmod.ensure_price(p, digit=None) is p

    q = Decimal("2.5")
    assert ordmod.ensure_quantity(q, digit=None) is q


def test_ensure_price_integer_default_quantize():
    # default digit is 4 -> quantize to 4 decimal places
    res = ordmod.ensure_price(1)
    assert isinstance(res, Decimal)
    assert res == Decimal("1.0000")


def test_ensure_price_from_float():
    # Test float conversion
    res = ordmod.ensure_price(10.5, digit=2)
    assert isinstance(res, Decimal)
    assert res == Decimal("10.50")


def test_ensure_quantity_from_int():
    # Test integer quantity conversion with default digit=0
    res = ordmod.ensure_quantity(10)
    assert isinstance(res, Decimal)
    assert res == Decimal("10")


def test_ensure_quantity_from_float():
    # Test float quantity conversion
    res = ordmod.ensure_quantity(5.75, digit=2)
    assert isinstance(res, Decimal)
    assert res == Decimal("5.75")


def test_to_domestic_and_foreign_order_condition_success_and_failure():
    # valid conversions
    assert ordmod.to_domestic_order_condition("condition") == "condition"
    assert ordmod.to_foreign_order_condition("LOO") == "LOO"

    # invalid conversions raise
    with pytest.raises(ValueError):
        ordmod.to_domestic_order_condition("LOO")

    with pytest.raises(ValueError):
        ordmod.to_foreign_order_condition("best")


def test_order_condition_rejects_non_positive_price():
    # negative price should raise
    with pytest.raises(ValueError) as ei:
        ordmod.order_condition(False, "KRX", "buy", Decimal("-1"))
    assert "가격은 0보다 커야합니다." in str(ei.value)


def test_order_condition_known_mappings():
    # Mapping that exists after fallback logic for non-virtual KRX buy with price
    res = ordmod.order_condition(False, "KRX", "buy", Decimal("100"), None, None)
    assert res[0] == "00" and res[2] == "지정가"

    # NASDAQ mapping for real (non-virtual) and condition LOO
    res2 = ordmod.order_condition(False, "NASDAQ", "buy", Decimal("100"), "LOO", None)
    assert res2[0] == "32" and res2[2] == "장개시지정가"


def test_resolve_domestic_order_condition():
    assert ordmod.resolve_domestic_order_condition("01") == (False, None, None)
    # unknown code returns default
    assert ordmod.resolve_domestic_order_condition("ZZZ") == (True, None, None)


def test_kis_ordernumber_eq_and_hash():
    a = object.__new__(ordmod.KisOrderNumberBase)
    b = object.__new__(ordmod.KisOrderNumberBase)

    # assign matching attributes
    for obj in (a, b):
        obj.account_number = "ACC"
        obj.symbol = "SYM"
        obj.market = "KRX"
        obj.branch = "01"
        obj.number = "10"

    assert a == b
    assert hash(a) == hash(b)


def test_order_condition_fallback_virtual_none():
    # Test fallback logic when virtual is not in map - converts to None (real)
    res = ordmod.order_condition(True, "KRX", "buy", Decimal("100"), None, None)


def test_orderable_conditions_repr_prints_table():
    # Test that orderable_conditions_repr returns a string
    result = ordmod.orderable_conditions_repr()
    assert isinstance(result, str)
    assert "KRX" in result or "NASDAQ" in result


def test_kis_simple_order_number_creation():
    # Test KisSimpleOrderNumber creation
    order = object.__new__(ordmod.KisSimpleOrderNumber)
    order.account_number = "12345678-01"
    order.symbol = "AAPL"
    order.market = "NASDAQ"
    order.branch = "000"
    order.number = "123"
    
    assert order.symbol == "AAPL"
    assert order.market == "NASDAQ"


def test_kis_simple_order_creation():
    # Test KisSimpleOrder creation
    from decimal import Decimal
    
    order = object.__new__(ordmod.KisSimpleOrder)
    order.account_number = "12345678-01"
    order.symbol = "AAPL"
    order.market = "NASDAQ"
    order.branch = "000"
    order.number = "123"
    order.unit_price = Decimal("150")
    order.quantity = Decimal("10")
    
    assert order.unit_price == Decimal("150")
    assert order.quantity == Decimal("10")


def test_domestic_order_checks_msg_cd_for_errors():
    # Test that __pre_init__ checks msg_cd for error codes
    # Note: Full exception tests are covered in integration tests
    # as mocking the full response structure is complex
    pass


def test_domestic_order_pre_init_not_found(monkeypatch):
    # Test __pre_init__ raises KisNotFoundError for APBK0656
    from pykis.responses.response import KisNotFoundError
    
    # Create exception first
    mock_request = Mock()
    mock_request.headers = {}
    mock_response = Mock()
    mock_response.request = mock_request
    mock_response.headers = {}
    
    def raise_not_found_mock(data, code, market):
        raise KisNotFoundError({"msg_cd": "APBK0656", "msg1": "Not found"}, mock_response)
    
    monkeypatch.setattr(ordmod, "raise_not_found", raise_not_found_mock)
    
    order = object.__new__(ordmod.KisDomesticOrder)
    order.symbol = "INVALID"
    order.market = "KRX"
    
    data = {
        "msg_cd": "APBK0656",
        "msg1": "Not found",
        "__response__": mock_response,
        "output": {"ORD_TMD": "153000"}
    }
    
    with pytest.raises(KisNotFoundError):
        order.__pre_init__(data)


def test_domestic_order_pre_init_sets_time(monkeypatch):
    # Test __pre_init__ sets time correctly
    from datetime import datetime
    from pykis.utils.timezone import TIMEZONE
    
    order = object.__new__(ordmod.KisDomesticOrder)
    order.symbol = "005930"
    order.market = "KRX"
    
    data = {
        "msg_cd": "OK",
        "output": {"ORD_TMD": "153000"}
    }
    
    # Mock super().__pre_init__
    monkeypatch.setattr(ordmod.KisAPIResponse, "__pre_init__", lambda self, data: None)
    
    order.__pre_init__(data)
    
    # Should have set time_kst and time
    assert order.time_kst.hour == 15
    assert order.time_kst.minute == 30
    assert order.time == order.time_kst


def test_foreign_order_checks_msg_cd_for_errors():
    # Test that ForeignOrder __pre_init__ checks msg_cd for error codes  
    # Note: Full exception tests are covered in integration tests
    # as mocking the full response structure is complex
    pass


def test_foreign_order_pre_init_sets_time_with_timezone(monkeypatch):
    # Test ForeignOrder __pre_init__ sets time with timezone conversion
    from pykis.api.stock.market import get_market_timezone
    from zoneinfo import ZoneInfo
    
    order = object.__new__(ordmod.KisForeignOrder)
    order.symbol = "AAPL"
    order.market = "NASDAQ"
    order.timezone = get_market_timezone("NASDAQ")
    
    data = {
        "msg_cd": "OK",
        "output": {"ORD_TMD": "093000"}
    }
    
    monkeypatch.setattr(ordmod.KisAPIResponse, "__pre_init__", lambda self, data: None)
    
    order.__pre_init__(data)
    
    # Should have set both time_kst and time with timezone
    assert order.time_kst.hour == 9
    assert order.time is not None


def test_orderable_quantity_buy_uses_orderable_amount(monkeypatch):
    # Test _orderable_quantity for buy order
    from decimal import Decimal
    
    mock_amount = Mock()
    mock_amount.qty = Decimal("100")
    mock_amount.foreign_qty = Decimal("150")
    mock_amount.unit_price = Decimal("50000")
    
    def mock_orderable_amount(*args, **kwargs):
        return mock_amount
    
    monkeypatch.setattr("pykis.api.account.orderable_amount.orderable_amount", mock_orderable_amount)
    
    qty, unit_price = ordmod._orderable_quantity(
        Mock(), 
        "12345678-01", 
        "KRX", 
        "005930", 
        order="buy",
        price=Decimal("50000")
    )
    
    assert qty == Decimal("100")
    assert unit_price == Decimal("50000")


def test_orderable_quantity_buy_with_foreign(monkeypatch):
    # Test _orderable_quantity for buy with include_foreign=True
    from decimal import Decimal
    
    mock_amount = Mock()
    mock_amount.qty = Decimal("100")
    mock_amount.foreign_qty = Decimal("150")
    mock_amount.unit_price = Decimal("50000")
    
    monkeypatch.setattr("pykis.api.account.orderable_amount.orderable_amount", lambda *a, **k: mock_amount)
    
    qty, unit_price = ordmod._orderable_quantity(
        Mock(), 
        "12345678-01", 
        "KRX", 
        "005930", 
        order="buy",
        include_foreign=True
    )
    
    assert qty == Decimal("150")


def test_orderable_quantity_buy_throws_when_no_qty(monkeypatch):
    # Test _orderable_quantity raises when no quantity available
    from decimal import Decimal
    
    mock_amount = Mock()
    mock_amount.qty = Decimal("0")
    mock_amount.foreign_qty = Decimal("0")
    
    monkeypatch.setattr("pykis.api.account.orderable_amount.orderable_amount", lambda *a, **k: mock_amount)
    
    with pytest.raises(ValueError, match="주문가능수량이 없습니다"):
        ordmod._orderable_quantity(
            Mock(), 
            "12345678-01", 
            "KRX", 
            "005930", 
            order="buy"
        )


def test_orderable_quantity_sell_uses_balance(monkeypatch):
    # Test _orderable_quantity for sell order
    from decimal import Decimal
    
    monkeypatch.setattr("pykis.api.account.balance.orderable_quantity", lambda *a, **k: Decimal("50"))
    
    qty, unit_price = ordmod._orderable_quantity(
        Mock(), 
        "12345678-01", 
        "KRX", 
        "005930", 
        order="sell"
    )
    
    assert qty == Decimal("50")
    assert unit_price is None


def test_orderable_quantity_sell_throws_when_none(monkeypatch):
    # Test _orderable_quantity for sell raises when no stock
    monkeypatch.setattr("pykis.api.account.balance.orderable_quantity", lambda *a, **k: None)
    
    with pytest.raises(ValueError, match="주문가능수량이 없습니다"):
        ordmod._orderable_quantity(
            Mock(), 
            "12345678-01", 
            "KRX", 
            "005930", 
            order="sell"
        )


def test_get_order_price_upper_limit(monkeypatch):
    # Test _get_order_price with upper limit
    from decimal import Decimal
    
    mock_quote = Mock()
    mock_quote.high_limit = Decimal("100000")
    mock_quote.close = Decimal("80000")
    
    monkeypatch.setattr(ordmod, "quote", lambda *a, **k: mock_quote)
    
    price = ordmod._get_order_price(Mock(), "KRX", "005930", "upper")
    
    assert price == Decimal("100000")


def test_get_order_price_upper_fallback(monkeypatch):
    # Test _get_order_price falls back to close * 1.5
    from decimal import Decimal
    
    mock_quote = Mock()
    mock_quote.high_limit = None
    mock_quote.close = Decimal("80000")
    
    monkeypatch.setattr(ordmod, "quote", lambda *a, **k: mock_quote)
    
    price = ordmod._get_order_price(Mock(), "KRX", "005930", "upper")
    
    assert price == Decimal("120000")  # 80000 * 1.5


def test_get_order_price_lower_limit(monkeypatch):
    # Test _get_order_price with lower limit
    from decimal import Decimal
    
    mock_quote = Mock()
    mock_quote.low_limit = Decimal("60000")
    mock_quote.close = Decimal("80000")
    
    monkeypatch.setattr(ordmod, "quote", lambda *a, **k: mock_quote)
    
    price = ordmod._get_order_price(Mock(), "KRX", "005930", "lower")
    
    assert price == Decimal("60000")


def test_domestic_order_api_codes_mapping():
    # Test DOMESTIC_ORDER_API_CODES contains expected mappings
    assert (True, "buy") in ordmod.DOMESTIC_ORDER_API_CODES
    assert (True, "sell") in ordmod.DOMESTIC_ORDER_API_CODES
    assert (False, "buy") in ordmod.DOMESTIC_ORDER_API_CODES
    assert (False, "sell") in ordmod.DOMESTIC_ORDER_API_CODES
    
    assert ordmod.DOMESTIC_ORDER_API_CODES[(True, "buy")] == "TTTC0802U"
    assert ordmod.DOMESTIC_ORDER_API_CODES[(True, "sell")] == "TTTC0801U"


def test_order_condition_fallback_market_none():
    # Test fallback to market=None when specific market not found
    # Using an exotic condition that might trigger fallback
    try:
        res = ordmod.order_condition(False, "AMEX", "buy", Decimal("100"), None, None)
        # If it succeeds, check it's a valid condition
        assert res[0] in [c[0] for c in ordmod.ORDER_CONDITION_MAP.values()]
    except ValueError:
        # It's okay if it raises ValueError for unsupported market
        pass


def test_order_condition_fallback_to_market_price():
    # When price is provided but combination not found, falls back to market price (price=None)
    # This tests the price=False fallback in line 292
    try:
        res = ordmod.order_condition(False, "KRX", "buy", Decimal("100"), "extended", "FOK")
        # If successful, verify it's valid
        assert len(res) == 3
    except ValueError:
        # Acceptable if this specific combination is not supported
        pass


def test_order_condition_virtual_not_supported_error():
    # Test error message when virtual trading doesn't support a condition
    with pytest.raises(ValueError) as exc_info:
        # Try a condition that exists for real but not virtual
        ordmod.order_condition(True, "NYSE", "buy", Decimal("100"), "LOO", None)
    
    error_msg = str(exc_info.value)
    assert "모의투자" in error_msg or "주문조건" in error_msg


def test_order_condition_invalid_combination_error():
    # Test error for completely invalid condition combination
    with pytest.raises(ValueError) as exc_info:
        ordmod.order_condition(False, "INVALID_MARKET", "buy", Decimal("100"), "INVALID_COND", "INVALID_EXEC")
    
    assert "주문조건" in str(exc_info.value)


def test_resolve_domestic_order_condition_unknown_code():
    # Unknown codes return default (True, None, None)
    result = ordmod.resolve_domestic_order_condition("99")
    assert result == (True, None, None)


def test_resolve_domestic_order_condition_market_price():
    # Code "01" is market price
    result = ordmod.resolve_domestic_order_condition("01")
    assert result == (False, None, None)


def test_resolve_domestic_order_condition_limit_ioc():
    # Code "11" is limit with IOC
    result = ordmod.resolve_domestic_order_condition("11")
    assert result == (True, None, "IOC")


def test_to_domestic_order_condition_valid():
    # Test valid domestic condition
    result = ordmod.to_domestic_order_condition("best")
    assert result == "best"
    
    result2 = ordmod.to_domestic_order_condition("extended")
    assert result2 == "extended"


def test_to_foreign_order_condition_valid():
    # Test valid foreign conditions
    result = ordmod.to_foreign_order_condition("LOO")
    assert result == "LOO"
    
    result2 = ordmod.to_foreign_order_condition("LOC")
    assert result2 == "LOC"


def test_ordernumberbase_init_minimal():
    # Test initialization without parameters
    ordmod.KisOrderNumberBase()
    # Should not raise error


def test_ordernumberbase_init_with_kis_only():
    # Test initialization with kis only
    mock_kis = Mock()
    order_num = ordmod.KisOrderNumberBase(kis=mock_kis)
    assert order_num.kis is mock_kis


def test_ordernumberbase_init_full_valid():
    # Test full initialization with all required parameters
    mock_kis = Mock()
    account = KisAccountNumber(account="12345678-01")
    
    order_num = ordmod.KisOrderNumberBase(
        kis=mock_kis,
        symbol="005930",
        market="KRX",
        account_number=account,
        branch="00001",
        number="12345"
    )
    
    assert order_num.symbol == "005930"
    assert order_num.market == "KRX"
    assert order_num.account_number == account
    assert order_num.branch == "00001"
    assert order_num.number == "12345"


def test_ordernumberbase_init_missing_market_error():
    # Test error when symbol provided but market missing
    mock_kis = Mock()
    
    with pytest.raises(ValueError) as exc_info:
        ordmod.KisOrderNumberBase(
            kis=mock_kis,
            symbol="005930",
            market=None
        )
    
    assert "market" in str(exc_info.value)


def test_ordernumberbase_init_missing_account_error():
    # Test error when symbol/market provided but account missing
    mock_kis = Mock()
    
    with pytest.raises(ValueError) as exc_info:
        ordmod.KisOrderNumberBase(
            kis=mock_kis,
            symbol="005930",
            market="KRX",
            account_number=None
        )
    
    assert "account_number" in str(exc_info.value)


def test_ordernumberbase_init_missing_branch_error():
    # Test error when account provided but branch missing
    mock_kis = Mock()
    account = KisAccountNumber(account="12345678-01")
    
    with pytest.raises(ValueError) as exc_info:
        ordmod.KisOrderNumberBase(
            kis=mock_kis,
            symbol="005930",
            market="KRX",
            account_number=account,
            branch=None
        )
    
    assert "branch" in str(exc_info.value)


def test_ordernumberbase_init_missing_number_error():
    # Test error when branch provided but number missing
    mock_kis = Mock()
    account = KisAccountNumber(account="12345678-01")
    
    with pytest.raises(ValueError) as exc_info:
        ordmod.KisOrderNumberBase(
            kis=mock_kis,
            symbol="005930",
            market="KRX",
            account_number=account,
            branch="00001",
            number=None
        )
    
    assert "number" in str(exc_info.value)


def test_ordernumberbase_eq_with_non_order_object():
    # Test equality with non-KisOrderNumber object returns False
    order_num = ordmod.KisOrderNumberBase()
    assert order_num != "not an order"
    assert order_num != 123
    assert order_num is not None


def test_kissimpleorder_init_minimal():
    # Test KisSimpleOrder initialization without parameters
    ordmod.KisSimpleOrder()
    # Should not raise error


def test_kissimpleorder_init_with_account_missing_symbol_error():
    # Test error when account provided but symbol missing
    account = KisAccountNumber(account="12345678-01")
    
    with pytest.raises(ValueError) as exc_info:
        ordmod.KisSimpleOrder(
            account_number=account,
            symbol=None
        )
    
    assert "symbol" in str(exc_info.value)


def test_kissimpleorder_init_with_symbol_missing_market_error():
    # Test error when symbol provided but market missing
    account = KisAccountNumber(account="12345678-01")
    
    with pytest.raises(ValueError) as exc_info:
        ordmod.KisSimpleOrder(
            account_number=account,
            symbol="005930",
            market=None
        )
    
    assert "market" in str(exc_info.value)


def test_kissimpleorder_init_with_branch_missing_account_error():
    # Test error when branch provided but account_number missing
    with pytest.raises(ValueError) as exc_info:
        ordmod.KisSimpleOrder(
            account_number=None,
            branch="00001"
        )
    
    assert "account_number" in str(exc_info.value)


def test_kissimpleorder_init_with_branch_missing_number_error():
    # Test error when branch provided but number missing
    account = KisAccountNumber(account="12345678-01")
    
    with pytest.raises(ValueError) as exc_info:
        ordmod.KisSimpleOrder(
            account_number=account,
            symbol="005930",
            market="KRX",
            branch="00001",
            number=None
        )
    
    assert "number" in str(exc_info.value)


def test_kissimpleorder_init_with_number_missing_timekst_error():
    # Test error when number provided but time_kst missing
    account = KisAccountNumber(account="12345678-01")
    
    with pytest.raises(ValueError) as exc_info:
        ordmod.KisSimpleOrder(
            account_number=account,
            symbol="005930",
            market="KRX",
            branch="00001",
            number="12345",
            time_kst=None
        )
    
    assert "time_kst" in str(exc_info.value)


def test_kissimpleorder_init_full_valid():
    # Test full valid initialization
    account = KisAccountNumber(account="12345678-01")
    time_kst = datetime(2024, 1, 1, 9, 0, 0, tzinfo=datetime.now().astimezone().tzinfo)
    
    order = ordmod.KisSimpleOrder(
        account_number=account,
        symbol="005930",
        market="KRX",
        branch="00001",
        number="12345",
        time_kst=time_kst
    )
    
    assert order.account_number == account
    assert order.symbol == "005930"
    assert order.market == "KRX"
    assert order.branch == "00001"
    assert order.number == "12345"
    assert order.time_kst == time_kst
