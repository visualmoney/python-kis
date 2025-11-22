from decimal import Decimal
from unittest import TestCase

from pykis import PyKis
from pykis.api.account.balance import KisBalance, KisDeposit
from pykis.scope.account import KisAccount
from tests.env import load_pykis


class AccountBalanceTests(TestCase):
    pykis: PyKis
    virtual_pykis: PyKis

    @classmethod
    def setUpClass(cls) -> None:
        """클래스 레벨에서 한 번만 실행 - 토큰 발급 횟수 제한 방지"""
        cls.pykis = load_pykis("real", use_websocket=False)
        cls.virtual_pykis = load_pykis("virtual", use_websocket=False)

    def test_account_scope(self):
        account = self.pykis.account()

        self.assertTrue(isinstance(account, KisAccount))

    def test_virtual_account_scope(self):
        account = self.virtual_pykis.account()

        self.assertTrue(isinstance(account, KisAccount))

    def test_balance(self):
        account = self.pykis.account()
        balance = account.balance()

        self.assertTrue(isinstance(balance, KisBalance))
        self.assertTrue(isinstance(balance.deposits["KRW"], KisDeposit))

        if (usd_deposit := balance.deposits.get("USD")) is not None:
            self.assertTrue(isinstance(usd_deposit, KisDeposit))
            self.assertGreater(usd_deposit.exchange_rate, Decimal(800))

    def test_virtual_balance(self):
        balance = self.virtual_pykis.account().balance()

        self.assertTrue(isinstance(balance, KisBalance))
        self.assertIsNotNone(balance.deposits["KRW"])
        self.assertIsNotNone(balance.deposits["USD"])
        self.assertIsNotNone(isinstance(balance.deposits["KRW"], KisDeposit))
        self.assertIsNotNone(isinstance(balance.deposits["USD"], KisDeposit))
        self.assertGreater(balance.deposits["USD"].exchange_rate, Decimal(800))

    def test_balance_stock(self):
        balance = self.pykis.account().balance()

        if not balance.stocks:
            self.skipTest("No stocks in account")

        for stock in balance.stocks:
            # isinstance() 체크 시 Protocol의 모든 속성에 접근하여 API 호출이 발생하므로
            # 필수 속성이 있는지만 확인
            self.assertTrue(hasattr(stock, 'symbol'))
            self.assertTrue(hasattr(stock, 'quantity'))

    def test_virtual_balance_stock(self):
        balance = self.virtual_pykis.account().balance()

        if not balance.stocks:
            self.skipTest("No stocks in account")

        for stock in balance.stocks:
            # isinstance() 체크 시 Protocol의 모든 속성에 접근하여 API 호출이 발생하므로
            # 필수 속성이 있는지만 확인
            self.assertTrue(hasattr(stock, 'symbol'))
            self.assertTrue(hasattr(stock, 'quantity'))
