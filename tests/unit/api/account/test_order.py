import pytest
from decimal import Decimal

from pykis.api.account import order as ordmod


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
