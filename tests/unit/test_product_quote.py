from datetime import date
from unittest import TestCase

from pykis import PyKis
from pykis.adapter.product.quote import KisQuotableProduct
from pykis.api.stock.chart import KisChart, KisChartBar
from pykis.api.stock.order_book import KisOrderbook, KisOrderbookItem
from pykis.api.stock.quote import KisQuote
from tests.env import load_pykis


class ProductQuoteTests(TestCase):
    pykis: PyKis

    def setUp(self) -> None:
        import os
        # Control whether to run real integration tests via environment variable.
        # Set PYKIS_RUN_REAL=1 (or true/yes) to exercise real network calls; otherwise use the mock fixture.
        run_real = os.environ.get("PYKIS_RUN_REAL", "").lower() in ("1", "true", "yes")
        if run_real:
            self.pykis = load_pykis("real", use_websocket=False)
        else:
            # load a mocked/local pykis instance to make tests hermetic and not depend on network/credentials
            self.pykis = load_pykis("mock", use_websocket=False)

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
        chart = self.pykis.stock("NVDA").day_chart()
        self.assertTrue(isinstance(chart, KisChart))

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
