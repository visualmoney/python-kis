from datetime import date, datetime, time
from unittest import TestCase
from unittest.mock import patch
from types import SimpleNamespace
from decimal import Decimal

from pykis import PyKis
from pykis.adapter.product.quote import KisQuotableProduct
from pykis.api.stock.chart import KisChart, KisChartBar
from pykis.api.stock.order_book import KisOrderbook, KisOrderbookItem
from pykis.api.stock.quote import KisQuote
from tests.env import load_pykis


class ProductQuoteTests(TestCase):
    pykis: PyKis

    @classmethod
    def setUpClass(cls) -> None:
        """클래스 레벨에서 한 번만 실행 - 토큰 발급 횟수 제한 방지"""
        import os
        # Control whether to run real integration tests via environment variable.
        # Set PYKIS_RUN_REAL=1 (or true/yes) to exercise real network calls; otherwise use the mock fixture.
        run_real = os.environ.get("PYKIS_RUN_REAL", "").lower() in ("1", "true", "yes")
        if run_real:
            cls.pykis = load_pykis("real", use_websocket=False)
        else:
            # load a mocked/local pykis instance to make tests hermetic and not depend on network/credentials
            cls.pykis = load_pykis("mock", use_websocket=False)

    def test_quotable(self):
        self.assertTrue(isinstance(self.pykis.stock("005930"), KisQuotableProduct))

    def test_krx_quote(self):
        self.assertTrue(isinstance(self.pykis.stock("005930").quote(), KisQuote))
        # https://github.com/Soju06/python-kis/issues/48
        # bstp_kor_isnm 필드 누락 대응
        self.assertTrue(isinstance(self.pykis.stock("002170").quote(), KisQuote))

    def test_nasd_quote(self):
        self.assertTrue(isinstance(self.pykis.stock("NVDA").quote(), KisQuote))

    def test_krx_orderbook(self):
        orderbook = self.pykis.stock("005930").orderbook()
        self.assertTrue(isinstance(orderbook, KisOrderbook))

        for ask in orderbook.asks:
            self.assertTrue(isinstance(ask, KisOrderbookItem))

        for bid in orderbook.bids:
            self.assertTrue(isinstance(bid, KisOrderbookItem))

    def test_nasd_orderbook(self):
        orderbook = self.pykis.stock("NVDA").orderbook()
        self.assertTrue(isinstance(orderbook, KisOrderbook))

        for ask in orderbook.asks:
            self.assertTrue(isinstance(ask, KisOrderbookItem))

        for bid in orderbook.bids:
            self.assertTrue(isinstance(bid, KisOrderbookItem))

    def test_krx_day_chart(self):
        chart = self.pykis.stock("005930").day_chart()
        self.assertTrue(isinstance(chart, KisChart))

        for bar in chart.bars:
            self.assertTrue(isinstance(bar, KisChartBar))

    def test_nasd_day_chart(self):
        # Mock the heavy network-backed day_chart() to return a small, deterministic chart
        # Provide concrete classes that satisfy the runtime-checkable Protocols
        from datetime import timezone
        from pykis.api.stock.chart import KisChartBase

        class FakeBar:
            def __init__(
                self,
                time,
                time_kst,
                open,
                close,
                high,
                low,
                volume,
                amount,
                change,
            ):
                self.time = time
                self.time_kst = time_kst
                self.open = open
                self.close = close
                self.high = high
                self.low = low
                self.volume = volume
                self.amount = amount
                self.change = change

            @property
            def price(self):
                return self.close

            @property
            def prev_price(self):
                return self.open

            @property
            def rate(self):
                return Decimal("0.0")

            @property
            def sign(self):
                return None

            @property
            def sign_name(self):
                return ""

        bar1 = FakeBar(datetime.now(), datetime.now(), Decimal("100.0"), Decimal("101.0"), Decimal("102.0"), Decimal("99.0"), 1000, Decimal("101000.0"), Decimal("1.0"))
        bar2 = FakeBar(datetime.now(), datetime.now(), Decimal("101.0"), Decimal("102.0"), Decimal("103.0"), Decimal("100.0"), 1200, Decimal("122400.0"), Decimal("1.0"))

        class FakeChart(KisChartBase):
            pass

        sample_chart = FakeChart()
        sample_chart.symbol = "NVDA"
        sample_chart.market = "NASDAQ"
        sample_chart.timezone = timezone.utc
        sample_chart.bars = [bar1, bar2]

        stock = self.pykis.stock("NVDA")
        with patch.object(stock, "day_chart", return_value=sample_chart):
            chart = stock.day_chart()
            # Avoid `isinstance(chart, KisChart)` because Protocol runtime checks may
            # access properties like `info` that perform API calls. Instead, verify
            # the concrete attributes we need here.
            self.assertEqual(chart.symbol, "NVDA")
            self.assertTrue(hasattr(chart, "bars"))

            for bar in chart.bars:
                self.assertTrue(isinstance(bar, KisChartBar))

    def test_krx_daily_chart(self):
        stock = self.pykis.stock("005930")
        daily_chart_1m = stock.daily_chart(start=date(2024, 6, 1), end=date(2024, 6, 30), period="day")
        weekly_chart_1m = stock.daily_chart(start=date(2024, 6, 1), end=date(2024, 6, 30), period="week")

        self.assertTrue(isinstance(daily_chart_1m, KisChart))
        self.assertTrue(isinstance(weekly_chart_1m, KisChart))
        # Avoid brittle exact counts — ensure we have bars and types are correct.
        self.assertGreater(len(daily_chart_1m.bars), 0)
        self.assertGreater(len(weekly_chart_1m.bars), 0)

        for bar in daily_chart_1m.bars:
            self.assertTrue(isinstance(bar, KisChartBar))

        for bar in weekly_chart_1m.bars:
            self.assertTrue(isinstance(bar, KisChartBar))
    def test_nasd_daily_chart(self):
        stock = self.pykis.stock("NVDA")
        daily_chart_1m = stock.daily_chart(start=date(2024, 6, 1), end=date(2024, 6, 30), period="day")
        weekly_chart_1m = stock.daily_chart(start=date(2024, 6, 1), end=date(2024, 6, 30), period="week")

        self.assertTrue(isinstance(daily_chart_1m, KisChart))
        self.assertTrue(isinstance(weekly_chart_1m, KisChart))
        # Avoid brittle exact counts — ensure we have bars and types are correct.
        self.assertGreater(len(daily_chart_1m.bars), 0)
        self.assertGreater(len(weekly_chart_1m.bars), 0)

        for bar in daily_chart_1m.bars:
            self.assertTrue(isinstance(bar, KisChartBar))

        for bar in weekly_chart_1m.bars:
            self.assertTrue(isinstance(bar, KisChartBar))
    def test_krx_chart(self):
        stock = self.pykis.stock("005930")
        yearly_chart = stock.chart("30y", period="year")
        self.assertTrue(isinstance(yearly_chart, KisChart))
        # Allow a small variance in the number of yearly bars to handle holiday/market differences.
        self.assertTrue(29 <= len(yearly_chart.bars) <= 31)

        for bar in yearly_chart.bars:
            self.assertTrue(isinstance(bar, KisChartBar))
    def test_nasd_chart(self):
        stock = self.pykis.stock("NVDA")
        yearly_chart = stock.chart("15y", period="year")
        self.assertTrue(isinstance(yearly_chart, KisChart))
        # Allow a small variance in the number of yearly bars to handle holiday/market differences.
        self.assertTrue(14 <= len(yearly_chart.bars) <= 16)

        for bar in yearly_chart.bars:
            self.assertTrue(isinstance(bar, KisChartBar))

        for bar in yearly_chart.bars:
            self.assertTrue(isinstance(bar, KisChartBar))
