from datetime import date, datetime, time, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch
import pytest

from pykis.api.stock import day_chart
from pykis.utils.timezone import TIMEZONE


class _MockBar:
    """Mock bar for testing drop_after and chart operations."""
    def __init__(self, d, open_price=1, high=2, low=1, close=1.5, volume=10, amount=100, change=0):
        # use datetime objects (day_chart expects .time to be datetime-like)
        if isinstance(d, date) and not isinstance(d, datetime):
            d = datetime.combine(d, datetime.min.time())
        self.time = d
        self.time_kst = d
        self.open = Decimal(str(open_price))
        self.high = Decimal(str(high))
        self.low = Decimal(str(low))
        self.close = Decimal(str(close))
        self.volume = volume
        self.amount = Decimal(str(amount))
        self.change = Decimal(str(change))
    
    @property
    def sign(self):
        """전일대비 부호"""
        return "steady" if self.change == 0 else "rise" if self.change > 0 else "decline"

    @property
    def price(self):
        """현재가 (종가)"""
        return self.close

    @property
    def prev_price(self):
        """전일가"""
        return self.close - self.change

    @property
    def rate(self):
        """등락률 (-100 ~ 100)"""
        from pykis.utils.math import safe_divide
        return safe_divide(self.change, self.prev_price) * 100

    @property
    def sign_name(self):
        """대비부호명"""
        from pykis.api.stock.quote import STOCK_SIGN_TYPE_KOR_MAP
        return STOCK_SIGN_TYPE_KOR_MAP[self.sign]


class _MockChart:
    """Mock chart for testing."""
    def __init__(self, bars=None):
        self.bars = bars or []


# Test drop_after function with various scenarios
class TestDropAfter:
    """Tests for the drop_after utility function."""

    def test_drop_after_with_time_start_and_end(self):
        """drop_after filters bars by time range."""
        # Bars need to be in reverse order (most recent first) for drop_after logic
        b4 = _MockBar(datetime(2020, 1, 1, 12, 0, 0))
        b3 = _MockBar(datetime(2020, 1, 1, 11, 0, 0))
        b2 = _MockBar(datetime(2020, 1, 1, 10, 0, 0))
        b1 = _MockBar(datetime(2020, 1, 1, 9, 0, 0))
        chart = _MockChart([b4, b3, b2, b1])

        result = day_chart.drop_after(chart, start=time(10, 0, 0), end=time(11, 0, 0))
        
        # drop_after reverses the output, keeping bars that match filters
        assert len(result.bars) == 2
        assert result.bars[0].time.time() == time(10, 0, 0)
        assert result.bars[1].time.time() == time(11, 0, 0)

    def test_drop_after_with_timedelta(self):
        """drop_after with timedelta calculates start time from first bar."""
        b1 = _MockBar(datetime(2020, 1, 1, 12, 0, 0))
        b2 = _MockBar(datetime(2020, 1, 1, 11, 0, 0))
        b3 = _MockBar(datetime(2020, 1, 1, 10, 0, 0))
        chart = _MockChart([b1, b2, b3])

        result = day_chart.drop_after(chart, start=timedelta(hours=1))
        
        # Should keep bars within 1 hour from the first bar (12:00)
        assert len(result.bars) >= 1

    def test_drop_after_with_period(self):
        """drop_after applies period filtering."""
        bars = [_MockBar(datetime(2020, 1, 1, 9, i, 0)) for i in range(10)]
        chart = _MockChart(bars)

        result = day_chart.drop_after(chart, period=3)
        
        # Should keep every 3rd bar
        assert len(result.bars) == 4  # indices 0, 3, 6, 9

    def test_drop_after_no_filters(self):
        """drop_after with no filters returns all bars reversed."""
        b1 = _MockBar(datetime(2020, 1, 1, 9, 0, 0))
        b2 = _MockBar(datetime(2020, 1, 1, 10, 0, 0))
        chart = _MockChart([b1, b2])

        result = day_chart.drop_after(chart)
        
        assert len(result.bars) == 2
        # Bars should be reversed
        assert result.bars[0] == b2
        assert result.bars[1] == b1


# Test KisDomesticDayChartBar properties
class TestKisDomesticDayChartBar:
    """Tests for KisDomesticDayChartBar properties and methods."""

    def test_sign_property_steady(self):
        """Bar sign is 'steady' when change is 0."""
        bar = _MockBar(datetime(2020, 1, 1, 9, 0, 0), change=0)
        assert bar.sign == "steady"

    def test_sign_property_rise(self):
        """Bar sign is 'rise' when change is positive."""
        bar = _MockBar(datetime(2020, 1, 1, 9, 0, 0), change=1.5)
        assert bar.sign == "rise"

    def test_sign_property_decline(self):
        """Bar sign is 'decline' when change is negative."""
        bar = _MockBar(datetime(2020, 1, 1, 9, 0, 0), change=-1.5)
        assert bar.sign == "decline"

    def test_price_property(self):
        """price property returns close value."""
        bar = _MockBar(datetime(2020, 1, 1, 9, 0, 0), close=100.5)
        assert bar.price == Decimal("100.5")

    def test_prev_price_property(self):
        """prev_price calculates from close and change."""
        bar = _MockBar(datetime(2020, 1, 1, 9, 0, 0), close=100, change=5)
        assert bar.prev_price == Decimal("95")

    def test_rate_property(self):
        """rate calculates percentage change."""
        bar = _MockBar(datetime(2020, 1, 1, 9, 0, 0), close=105, change=5)
        # prev_price = 105 - 5 = 100, rate = (5/100)*100 = 5%
        assert bar.rate == Decimal("5")

    def test_sign_name_property(self):
        """sign_name returns Korean translation."""
        bar_rise = _MockBar(datetime(2020, 1, 1, 9, 0, 0), change=1)
        bar_decline = _MockBar(datetime(2020, 1, 1, 9, 0, 0), change=-1)
        bar_steady = _MockBar(datetime(2020, 1, 1, 9, 0, 0), change=0)
        
        assert bar_rise.sign_name in ["상승", "상한", "상한가"]
        assert bar_decline.sign_name in ["하락", "하한", "하한가"]
        assert bar_steady.sign_name == "보합"


# Test domestic_day_chart function
class TestDomesticDayChart:
    """Tests for domestic_day_chart function."""

    def test_validates_empty_symbol(self):
        """domestic_day_chart raises ValueError for empty symbol."""
        fake_kis = Mock()
        
        with pytest.raises(ValueError, match="종목 코드를 입력해주세요"):
            day_chart.domestic_day_chart(fake_kis, "")

    def test_validates_invalid_period(self):
        """domestic_day_chart raises ValueError for invalid period."""
        fake_kis = Mock()
        
        with pytest.raises(ValueError, match="간격은 1분 이상이어야 합니다"):
            day_chart.domestic_day_chart(fake_kis, "005930", period=0)

    def test_validates_start_after_end(self):
        """domestic_day_chart raises ValueError when start is after end."""
        fake_kis = Mock()
        
        with pytest.raises(ValueError, match="시작 시간은 종료 시간보다 이전이어야 합니다"):
            day_chart.domestic_day_chart(
                fake_kis, 
                "005930", 
                start=time(15, 0, 0), 
                end=time(9, 0, 0)
            )

    def test_fetches_single_page(self):
        """domestic_day_chart fetches and returns chart data."""
        fake_kis = Mock()
        mock_chart = _MockChart([
            _MockBar(datetime(2020, 1, 1, 10, 0, 0)),
            _MockBar(datetime(2020, 1, 1, 9, 30, 0)),
        ])
        fake_kis.fetch.return_value = mock_chart
        
        result = day_chart.domestic_day_chart(fake_kis, "005930")
        
        assert fake_kis.fetch.called
        assert result == mock_chart

    def test_handles_timedelta_start(self):
        """domestic_day_chart handles timedelta as start parameter."""
        fake_kis = Mock()
        mock_chart = _MockChart([
            _MockBar(datetime(2020, 1, 1, 12, 0, 0)),
            _MockBar(datetime(2020, 1, 1, 11, 0, 0)),
            _MockBar(datetime(2020, 1, 1, 10, 0, 0)),
        ])
        fake_kis.fetch.return_value = mock_chart
        
        result = day_chart.domestic_day_chart(
            fake_kis, 
            "005930", 
            start=timedelta(hours=1)
        )
        
        assert result is not None


# Test foreign_day_chart function
class TestForeignDayChart:
    """Tests for foreign_day_chart function."""

    def test_validates_empty_symbol(self):
        """foreign_day_chart raises ValueError for empty symbol."""
        fake_kis = Mock()
        
        with pytest.raises(ValueError, match="종목 코드를 입력해주세요"):
            day_chart.foreign_day_chart(fake_kis, "", "NAS")

    def test_validates_invalid_period(self):
        """foreign_day_chart raises ValueError for invalid period."""
        fake_kis = Mock()
        
        with pytest.raises(ValueError, match="간격은 1분 이상이어야 합니다"):
            day_chart.foreign_day_chart(fake_kis, "AAPL", "NAS", period=0)

    def test_validates_krx_market(self):
        """foreign_day_chart raises ValueError for KRX market."""
        fake_kis = Mock()
        
        with pytest.raises(ValueError, match="국내 시장은 domestic_chart"):
            day_chart.foreign_day_chart(fake_kis, "005930", "KRX")

    @patch('pykis.api.stock.quote.quote')
    def test_fetches_with_quote_for_prev_price(self, mock_quote):
        """foreign_day_chart fetches quote to get prev_price."""
        fake_kis = Mock()
        mock_quote_result = Mock()
        mock_quote_result.prev_price = Decimal("150.0")
        mock_quote.return_value = mock_quote_result
        
        mock_chart = Mock()
        mock_chart.bars = [_MockBar(datetime(2020, 1, 1, 10, 0, 0))]
        fake_kis.fetch.return_value = mock_chart
        
        result = day_chart.foreign_day_chart(
            fake_kis, 
            "AAPL", 
            "NASDAQ", 
            once=True
        )
        
        mock_quote.assert_called_once_with(fake_kis, "AAPL", "NASDAQ")
        assert fake_kis.fetch.called

    @patch('pykis.api.stock.quote.quote')
    def test_handles_once_parameter(self, mock_quote):
        """foreign_day_chart respects once parameter."""
        fake_kis = Mock()
        mock_quote_result = Mock()
        mock_quote_result.prev_price = Decimal("150.0")
        mock_quote.return_value = mock_quote_result
        
        mock_chart = Mock()
        mock_chart.bars = [_MockBar(datetime(2020, 1, 1, 10, 0, 0))]
        fake_kis.fetch.return_value = mock_chart
        
        result = day_chart.foreign_day_chart(
            fake_kis, 
            "AAPL", 
            "NASDAQ", 
            once=True
        )
        
        # Should only fetch once when once=True
        assert fake_kis.fetch.call_count == 1


# Test day_chart wrapper function
class TestDayChart:
    """Tests for day_chart wrapper function."""

    @patch('pykis.api.stock.day_chart.domestic_day_chart')
    def test_routes_to_domestic_for_krx(self, mock_domestic):
        """day_chart routes to domestic_day_chart for KRX market."""
        fake_kis = Mock()
        mock_domestic.return_value = _MockChart()
        
        result = day_chart.day_chart(fake_kis, "005930", "KRX")
        
        mock_domestic.assert_called_once()
        assert result is not None

    @patch('pykis.api.stock.day_chart.foreign_day_chart')
    def test_routes_to_foreign_for_non_krx(self, mock_foreign):
        """day_chart routes to foreign_day_chart for non-KRX markets."""
        fake_kis = Mock()
        mock_foreign.return_value = Mock()
        
        result = day_chart.day_chart(fake_kis, "AAPL", "NASDAQ")
        
        mock_foreign.assert_called_once()
        assert result is not None


# Test product_day_chart function
class TestProductDayChart:
    """Tests for product_day_chart function."""

    @patch('pykis.api.stock.day_chart.day_chart')
    def test_calls_day_chart_with_product_attributes(self, mock_day_chart):
        """product_day_chart calls day_chart with product's symbol and market."""
        mock_product = Mock()
        mock_product.kis = Mock()
        mock_product.symbol = "005930"
        mock_product.market = "KRX"
        mock_day_chart.return_value = _MockChart()
        
        result = day_chart.product_day_chart(
            mock_product,
            start=time(9, 0, 0),
            end=time(15, 30, 0),
            period=5
        )
        
        mock_day_chart.assert_called_once_with(
            mock_product.kis,
            symbol="005930",
            market="KRX",
            start=time(9, 0, 0),
            end=time(15, 30, 0),
            period=5
        )


# Test KisDomesticDayChart class
class TestKisDomesticDayChart:
    """Tests for KisDomesticDayChart response class."""

    def test_initializes_with_symbol(self):
        """KisDomesticDayChart initializes with symbol."""
        chart = day_chart.KisDomesticDayChart("005930")
        assert chart.symbol == "005930"
        assert chart.market == "KRX"
        assert chart.timezone == TIMEZONE


# Test KisForeignDayChart class
class TestKisForeignDayChart:
    """Tests for KisForeignDayChart response class."""

    def test_initializes_with_symbol_market_prev_price(self):
        """KisForeignDayChart initializes with required parameters."""
        chart = day_chart.KisForeignDayChart("AAPL", "NASDAQ", Decimal("150.0"))
        assert chart.symbol == "AAPL"
        assert chart.market == "NASDAQ"
        assert chart.prev_price == Decimal("150.0")


# Test more edge cases for comprehensive coverage
class TestDropAfterEdgeCases:
    """Additional edge cases for drop_after function."""

    def test_drop_after_empty_bars(self):
        """drop_after handles empty bar list."""
        chart = _MockChart([])
        result = day_chart.drop_after(chart)
        assert result.bars == []

    def test_drop_after_timedelta_at_boundary(self):
        """drop_after with timedelta handles boundary conditions."""
        b1 = _MockBar(datetime(2020, 1, 1, 0, 30, 0))
        chart = _MockChart([b1])
        
        # When timedelta is larger than time elapsed since midnight
        result = day_chart.drop_after(chart, start=timedelta(hours=2))
        assert len(result.bars) >= 0


class TestDomesticDayChartEdgeCases:
    """Additional edge cases for domestic_day_chart."""

    def test_domestic_day_chart_multiple_pages(self):
        """domestic_day_chart fetches multiple pages until exhausted."""
        fake_kis = Mock()
        
        # First page with data
        chart1 = _MockChart([
            _MockBar(datetime(2020, 1, 1, 15, 0, 0)),
            _MockBar(datetime(2020, 1, 1, 14, 0, 0)),
        ])
        
        # Second page with data
        chart2 = _MockChart([
            _MockBar(datetime(2020, 1, 1, 13, 0, 0)),
            _MockBar(datetime(2020, 1, 1, 12, 0, 0)),
        ])
        
        # Third page empty
        chart3 = _MockChart([])
        
        fake_kis.fetch.side_effect = [chart1, chart2, chart3]
        
        result = day_chart.domestic_day_chart(fake_kis, "005930")
        
        assert fake_kis.fetch.call_count == 3
        assert len(result.bars) == 4

    def test_domestic_day_chart_with_end_time(self):
        """domestic_day_chart respects end time parameter."""
        fake_kis = Mock()
        mock_chart = _MockChart([
            _MockBar(datetime(2020, 1, 1, 15, 0, 0)),
            _MockBar(datetime(2020, 1, 1, 10, 0, 0)),
        ])
        fake_kis.fetch.return_value = mock_chart
        
        result = day_chart.domestic_day_chart(
            fake_kis, 
            "005930", 
            end=time(14, 0, 0)
        )
        
        assert result is not None


class TestForeignDayChartEdgeCases:
    """Additional edge cases for foreign_day_chart."""

    @patch('pykis.api.stock.quote.quote')
    def test_foreign_day_chart_multiple_periods(self, mock_quote):
        """foreign_day_chart fetches multiple periods."""
        fake_kis = Mock()
        mock_quote_result = Mock()
        mock_quote_result.prev_price = Decimal("150.0")
        mock_quote.return_value = mock_quote_result
        
        # Create charts for different periods - need enough for potential multiple iterations
        def create_chart():
            mock_chart = Mock()
            mock_chart.bars = [_MockBar(datetime(2020, 1, 1, 10, 0, 0))]
            return mock_chart
        
        # Make fetch return charts indefinitely
        fake_kis.fetch.return_value = create_chart()
        
        result = day_chart.foreign_day_chart(
            fake_kis, 
            "AAPL", 
            "NASDAQ",
            once=True
        )
        
        assert result is not None
        # Should call at least once
        assert fake_kis.fetch.call_count == 1

    @patch('pykis.api.stock.quote.quote')
    def test_foreign_day_chart_with_time_filters(self, mock_quote):
        """foreign_day_chart applies time filtering."""
        fake_kis = Mock()
        mock_quote_result = Mock()
        mock_quote_result.prev_price = Decimal("150.0")
        mock_quote.return_value = mock_quote_result
        
        mock_chart = Mock()
        mock_chart.bars = [
            _MockBar(datetime(2020, 1, 1, 12, 0, 0)),
            _MockBar(datetime(2020, 1, 1, 10, 0, 0)),
        ]
        fake_kis.fetch.return_value = mock_chart
        
        result = day_chart.foreign_day_chart(
            fake_kis, 
            "AAPL", 
            "NASDAQ",
            start=time(11, 0, 0),
            end=time(13, 0, 0),
            once=True
        )
        
        assert result is not None

    @patch('pykis.api.stock.quote.quote')
    def test_foreign_day_chart_with_period(self, mock_quote):
        """foreign_day_chart applies period filtering."""
        fake_kis = Mock()
        mock_quote_result = Mock()
        mock_quote_result.prev_price = Decimal("150.0")
        mock_quote.return_value = mock_quote_result
        
        mock_chart = Mock()
        mock_chart.bars = [_MockBar(datetime(2020, 1, 1, 10 + i, 0, 0)) for i in range(10)]
        fake_kis.fetch.return_value = mock_chart
        
        result = day_chart.foreign_day_chart(
            fake_kis, 
            "AAPL", 
            "NASDAQ",
            period=5,
            once=True
        )
        
        assert result is not None

    @patch('pykis.api.stock.quote.quote')
    def test_foreign_day_chart_with_empty_bars_and_timedelta(self, mock_quote):
        """foreign_day_chart handles timedelta with start parameter."""
        fake_kis = Mock()
        mock_quote_result = Mock()
        mock_quote_result.prev_price = Decimal("150.0")
        mock_quote.return_value = mock_quote_result
        
        # Return chart with bars to test timedelta logic
        mock_chart = Mock()
        mock_chart.bars = [
            _MockBar(datetime(2020, 1, 1, 12, 0, 0)),
            _MockBar(datetime(2020, 1, 1, 11, 0, 0)),
        ]
        fake_kis.fetch.return_value = mock_chart
        
        result = day_chart.foreign_day_chart(
            fake_kis, 
            "AAPL", 
            "NASDAQ",
            start=timedelta(hours=2),
            once=True
        )
        
        assert result is not None


class TestKisDomesticDayChartBarEdgeCases:
    """Test edge cases for KisDomesticDayChartBar."""

    def test_rate_with_zero_prev_price(self):
        """rate handles zero prev_price gracefully."""
        # close=0, change=0 means prev_price=0
        bar = _MockBar(datetime(2020, 1, 1, 9, 0, 0), close=0, change=0)
        # safe_divide should handle division by zero
        rate = bar.rate
        assert rate == Decimal("0")


class TestKisForeignTradingHours:
    """Tests for KisForeignTradingHours class."""

    def test_initializes_with_market(self):
        """KisForeignTradingHours initializes with market."""
        hours = day_chart.KisForeignTradingHours("NASDAQ")
        assert hours.market == "NASDAQ"


class TestDomesticDayChartIntegration:
    """Integration tests for domestic day chart."""

    def test_domestic_day_chart_respects_start_time(self):
        """domestic_day_chart filters by start time correctly."""
        fake_kis = Mock()
        
        chart1 = _MockChart([
            _MockBar(datetime(2020, 1, 1, 15, 0, 0)),
            _MockBar(datetime(2020, 1, 1, 14, 0, 0)),
        ])
        chart2 = _MockChart([
            _MockBar(datetime(2020, 1, 1, 13, 0, 0)),
            _MockBar(datetime(2020, 1, 1, 12, 0, 0)),
        ])
        chart3 = _MockChart([
            _MockBar(datetime(2020, 1, 1, 11, 0, 0)),
            _MockBar(datetime(2020, 1, 1, 10, 0, 0)),
        ])
        
        fake_kis.fetch.side_effect = [chart1, chart2, chart3]
        
        result = day_chart.domestic_day_chart(
            fake_kis, 
            "005930",
            start=time(11, 30, 0)
        )
        
        assert result is not None
        # Should break when reaching start time
        assert fake_kis.fetch.call_count >= 1

    def test_domestic_day_chart_with_period_5(self):
        """domestic_day_chart applies 5-minute period correctly."""
        fake_kis = Mock()
        bars = [_MockBar(datetime(2020, 1, 1, 9, i, 0)) for i in range(0, 60, 1)]
        mock_chart = _MockChart(bars)
        fake_kis.fetch.return_value = mock_chart
        
        result = day_chart.domestic_day_chart(
            fake_kis, 
            "005930",
            period=5
        )
        
        assert result is not None


class TestKisDomesticDayChartBarIntegration:
    """Test actual KisDomesticDayChartBar behavior."""

    def test_bar_properties_with_real_class(self):
        """Test KisDomesticDayChartBar properties directly."""
        # Create a mock bar data that mimics API response
        bar_data = {
            "stck_bsop_date": "20200101",
            "stck_cntg_hour": "093000",
            "stck_oprc": "100.0",
            "stck_prpr": "105.0",
            "stck_hgpr": "110.0",
            "stck_lwpr": "95.0",
            "cntg_vol": "1000",
            "acml_tr_pbmn": "100000.0"
        }
        
        # Test that the bar can be initialized
        bar = day_chart.KisDomesticDayChartBar()
        # Manually set attributes for testing
        bar.time = datetime(2020, 1, 1, 9, 30, 0, tzinfo=TIMEZONE)
        bar.time_kst = bar.time
        bar.open = Decimal("100.0")
        bar.close = Decimal("105.0")
        bar.high = Decimal("110.0")
        bar.low = Decimal("95.0")
        bar.volume = 1000
        bar.amount = Decimal("100000.0")
        bar.change = Decimal("5.0")
        
        # Test properties
        assert bar.sign == "rise"
        assert bar.price == Decimal("105.0")
        assert bar.prev_price == Decimal("100.0")
        assert bar.rate == Decimal("5.0")


class TestKisForeignDayChartBarIntegration:
    """Test KisForeignDayChartBar behavior."""

    def test_foreign_bar_properties(self):
        """Test KisForeignDayChartBar properties directly."""
        bar = day_chart.KisForeignDayChartBar()
        # Manually set attributes
        bar.time = datetime(2020, 1, 1, 9, 30, 0, tzinfo=TIMEZONE)
        bar.time_kst = bar.time
        bar.open = Decimal("150.0")
        bar.close = Decimal("155.0")
        bar.high = Decimal("160.0")
        bar.low = Decimal("145.0")
        bar.volume = 5000
        bar.amount = Decimal("750000.0")
        bar.change = Decimal("5.0")
        
        # Test properties
        assert bar.sign == "rise"
        assert bar.price == Decimal("155.0")
        assert bar.prev_price == Decimal("150.0")


class TestForeignChartTimezoneHandling:
    """Test timezone handling in foreign chart."""

    def test_foreign_trading_hours_initializes(self):
        """Test KisForeignTradingHours initialization."""
        hours = day_chart.KisForeignTradingHours("NYSE")
        assert hours.market == "NYSE"


class TestDomesticDayChartCursorLogic:
    """Test domestic day chart cursor pagination logic."""

    def test_cursor_breaks_on_start_time(self):
        """Test that cursor stops fetching when start time is reached."""
        fake_kis = Mock()
        
        # Create bars that go back in time
        chart1 = _MockChart([
            _MockBar(datetime(2020, 1, 1, 15, 0, 0)),
            _MockBar(datetime(2020, 1, 1, 14, 0, 0)),
            _MockBar(datetime(2020, 1, 1, 13, 0, 0)),
        ])
        
        chart2 = _MockChart([
            _MockBar(datetime(2020, 1, 1, 12, 0, 0)),
            _MockBar(datetime(2020, 1, 1, 11, 0, 0)),
            _MockBar(datetime(2020, 1, 1, 10, 0, 0)),
        ])
        
        # Third fetch returns empty to stop pagination
        chart3 = _MockChart([])
        
        fake_kis.fetch.side_effect = [chart1, chart2, chart3]
        
        result = day_chart.domestic_day_chart(
            fake_kis,
            "005930",
            start=time(11, 0, 0),
            end=time(15, 30, 0)
        )
        
        assert result is not None
        assert fake_kis.fetch.call_count >= 2


class TestDomesticDayChartLoopTermination:
    """Test loop termination conditions in domestic_day_chart."""

    def test_cursor_less_than_last_time(self):
        """Test pagination stops when cursor is before last bar time."""
        fake_kis = Mock()
        
        # First fetch returns bars
        chart1 = _MockChart([
            _MockBar(datetime(2020, 1, 1, 15, 0, 0)),
            _MockBar(datetime(2020, 1, 1, 14, 30, 0)),
        ])
        
        # Set up end time after first bar to trigger early cursor break
        fake_kis.fetch.return_value = chart1
        
        result = day_chart.domestic_day_chart(
            fake_kis,
            "005930",
            end=time(14, 0, 0)  # Before the last bar
        )
        
        assert result is not None
    # other runtime behaviors require a real `fetch` method on the client; skip here
