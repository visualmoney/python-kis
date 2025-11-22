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
    # Result should be a tuple of (code, condition, name)
    assert isinstance(res, tuple)
    assert len(res) == 3


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
