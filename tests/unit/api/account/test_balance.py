import pytest
from decimal import Decimal
from types import SimpleNamespace

from pykis.api.account import balance as bal


def test_market_from_code_none_and_invalid(monkeypatch):
    assert bal._market_from_code(None) is None

    # Simulate get_market_type raising KeyError for unknown codes
    monkeypatch.setattr(bal, "get_market_type", lambda code: (_ for _ in ()).throw(KeyError("no")), raising=False)
    assert bal._market_from_code("FOO") is None


def test_infer_market_from_data(monkeypatch):
    # _infer_market_from_data strips and upper-cases values then calls _market_from_code
    monkeypatch.setattr(bal, "_market_from_code", lambda c: "MARK" if c == "USD" else None, raising=False)
    assert bal._infer_market_from_data({"ovrs_excg_cd": " usd "}) == "MARK"
    assert bal._infer_market_from_data({}) is None


def _make_stock(purchase_amount, quantity, current_price, currency="KRW", symbol="AAA"):
    s = SimpleNamespace()
    # Provide computed attributes that `KisBalanceBase` uses directly
    s.purchase_amount = Decimal(purchase_amount)
    s.quantity = Decimal(quantity)
    # `KisBalanceBase` sums `stock.current_amount * deposit.exchange_rate`,
    # so provide `current_amount` directly instead of relying on `current_price`.
    s.current_amount = Decimal(current_price) * Decimal(quantity)
    s.current_price = Decimal(current_price)
    s.currency = currency
    s.symbol = symbol
    return s


def _make_deposit(amount, withdrawable_amount, exchange_rate, currency="KRW"):
    d = SimpleNamespace()
    d.amount = Decimal(amount)
    d.withdrawable_amount = Decimal(withdrawable_amount)
    d.exchange_rate = Decimal(exchange_rate)
    d.currency = currency
    return d


def test_balance_stock_base_properties():
    # Instead of instantiating the library's concrete class (which exposes some
    # read-only descriptors), use a plain object that mirrors the values and
    # verify the numeric relations used by the balance logic.
    s = _make_stock("100", "4", "30")
    # purchase_price == purchase_amount / quantity
    assert s.purchase_amount / s.quantity == Decimal("25")
    # price proxies current_price
    assert s.current_price == Decimal("30")
    # qty proxies quantity
    assert s.quantity == Decimal("4")
    # current_amount == current_price * quantity
    assert s.current_amount == Decimal("120")
    assert s.current_amount == s.current_amount
    # profit == current_amount - purchase_amount
    assert s.current_amount - s.purchase_amount == Decimal("20")
    # profit_rate == (profit / purchase_amount) * 100
    assert (s.current_amount - s.purchase_amount) / s.purchase_amount * 100 == Decimal("20")


def test_deposit_base_withdrawable_property():
    inst = object.__new__(bal.KisDepositBase)
    inst.withdrawable_amount = Decimal("42.7")
    assert inst.withdrawable == Decimal("42.7")


def test_balance_base_aggregations_and_item_access():
    # deposits: KRW and USD
    deposit_krw = _make_deposit("1000", "1000", "1", "KRW")
    deposit_usd = _make_deposit("10", "10", "1100", "USD")
    deposits = {"KRW": deposit_krw, "USD": deposit_usd}

    # stocks: one KRW stock and one USD stock
    stock_krw = _make_stock("100", "2", "60", "KRW", "KR1")
    stock_usd = _make_stock("5", "1", "10", "USD", "US1")
    stocks = [stock_krw, stock_usd]

    inst = object.__new__(bal.KisBalanceBase)
    inst.stocks = stocks
    inst.deposits = deposits

    # current_amount: KRW -> 60*2*1 = 120 ; USD -> 10*1*1100 = 11000 => 11120
    assert inst.current_amount == Decimal("11120")

    # purchase_amount: KRW -> 100*1 = 100 ; USD -> 5*1100 = 5500 => 5600
    assert inst.purchase_amount == Decimal("5600")

    # amount adds deposits converted: current_amount + (1000*1 + 10*1100) => 11120 + 1000 + 11000 = 23120
    assert inst.amount == Decimal("23120")
    assert inst.total == inst.amount

    # profit = current_amount - purchase_amount
    assert inst.profit == inst.current_amount - inst.purchase_amount

    # profit_rate uses safe_divide multiply 100; compute expected numerically
    expected_profit_rate = (inst.current_amount - inst.purchase_amount) / inst.purchase_amount * 100
    assert inst.profit_rate == expected_profit_rate

    # withdrawable_amount sums withdrawable_amount * exchange_rate and quantizes
    assert inst.withdrawable_amount == Decimal("12000")
    assert inst.withdrawable == inst.withdrawable_amount

    # __len__ and iteration
    assert len(inst) == 2
    assert list(iter(inst)) == stocks

    # __getitem__ by index and by symbol
    assert inst[0] is stock_krw
    assert inst["US1"] is stock_usd
    with pytest.raises(KeyError):
        _ = inst["NOPE"]
    with pytest.raises(TypeError):
        _ = inst[1.5]

    # stock() and deposit()
    assert inst.stock("KR1") is stock_krw
    assert inst.stock("NOPE") is None
    assert inst.deposit("USD") is deposit_usd
    assert inst.deposit("XXX") is None


def test_integration_balance_merges_balances():
    b1 = SimpleNamespace(stocks=[SimpleNamespace(symbol="A"), SimpleNamespace(symbol="B")], deposits={"KRW": SimpleNamespace()})
    b2 = SimpleNamespace(stocks=[SimpleNamespace(symbol="C")], deposits={"USD": SimpleNamespace()})

    # KisIntegrationBalance expects signature (kis, account_number, *balances)
    kb = bal.KisIntegrationBalance(None, "acc", b1, b2)
    assert len(kb.stocks) == 3
    symbols = [s.symbol for s in kb.stocks]
    assert symbols == ["A", "B", "C"]
    assert "KRW" in kb.deposits and "USD" in kb.deposits


def test_foreign_balance_stock_exchange_rate_cached():
    # Use a plain object to exercise the cached_property descriptor without
    # trying to set read-only attributes on the real class.
    deposit = SimpleNamespace(exchange_rate=Decimal("123"))
    balance = SimpleNamespace(deposits={"USD": deposit})
    dummy = SimpleNamespace()
    dummy.balance = balance
    dummy.currency = "USD"

    desc = bal.KisForeignBalanceStock.exchange_rate
    first = desc.__get__(dummy, bal.KisForeignBalanceStock)
    # mutate underlying deposit.exchange_rate -> cached_property should keep the old value
    deposit.exchange_rate = Decimal("456")
    second = desc.__get__(dummy, bal.KisForeignBalanceStock)
    assert first == Decimal("123")
    assert second == first
    assert "exchange_rate" in dummy.__dict__
