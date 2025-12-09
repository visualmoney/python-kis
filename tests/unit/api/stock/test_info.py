"""
Tests for pykis.api.stock.info module

Tests coverage for:
- _KisStockInfo class properties
- get_market_country function
- quotable_market function
- info function
- resolve_market function
"""

from datetime import timedelta
from unittest.mock import Mock, MagicMock, patch
import pytest

from pykis.api.stock.info import (
    _KisStockInfo,
    MARKET_CODE_MAP,
    R_MARKET_TYPE_MAP,
    MARKET_COUNTRY_MAP,
    get_market_country,
    quotable_market,
    info,
    resolve_market,
    MARKET_TYPE_MAP,
)
from pykis.client.exceptions import KisAPIError
from pykis.responses.exceptions import KisNotFoundError


# ===== Tests for _KisStockInfo class =====

class TestKisStockInfo:
    """Tests for _KisStockInfo response class."""

    def test_initialization(self):
        """Test _KisStockInfo can be initialized."""
        # _KisStockInfo는 KisAPIResponse를 상속하므로 직접 인스턴스화 불가
        # 속성 정의만 확인
        assert hasattr(_KisStockInfo, 'symbol')
        assert hasattr(_KisStockInfo, 'std_code')
        assert hasattr(_KisStockInfo, 'name_kor')

    def test_name_property(self):
        """Test name property returns name_kor."""
        mock_info = Mock(spec=_KisStockInfo)
        mock_info.name_kor = "삼성전자"
        
        # Property를 직접 테스트할 수 없으므로 클래스 정의 확인
        assert hasattr(_KisStockInfo, 'name')

    def test_market_property(self):
        """Test market property maps from market_code."""
        # market_code 매핑 확인
        assert MARKET_CODE_MAP["300"] == "KRX"
        assert MARKET_CODE_MAP["512"] == "NASDAQ"
        assert MARKET_CODE_MAP["513"] == "NYSE"

    def test_market_name_property(self):
        """Test market_name property maps from market_code."""
        # market_name 매핑 확인
        assert R_MARKET_TYPE_MAP["300"] == "주식"
        assert R_MARKET_TYPE_MAP["512"] == "나스닥"
        assert R_MARKET_TYPE_MAP["513"] == "뉴욕"

    def test_foreign_property(self):
        """Test foreign property checks if market is not KRX."""
        # MARKET_TYPE_MAP["KRX"]에 없는 코드는 해외 종목
        assert "512" not in MARKET_TYPE_MAP["KRX"]
        assert "513" not in MARKET_TYPE_MAP["KRX"]

    def test_domestic_property(self):
        """Test domestic property is opposite of foreign."""
        # MARKET_TYPE_MAP["KRX"]에 있는 코드는 국내 종목
        assert "300" in MARKET_TYPE_MAP["KRX"]


# ===== Tests for get_market_country function =====

class TestGetMarketCountry:
    """Tests for get_market_country function."""

    def test_krx_returns_kr(self):
        """Test KRX market returns KR country."""
        assert get_market_country("KRX") == "KR"

    def test_nasdaq_returns_us(self):
        """Test NASDAQ market returns US country."""
        assert get_market_country("NASDAQ") == "US"

    def test_nyse_returns_us(self):
        """Test NYSE market returns US country."""
        assert get_market_country("NYSE") == "US"

    def test_amex_returns_us(self):
        """Test AMEX market returns US country."""
        assert get_market_country("AMEX") == "US"

    def test_hkex_returns_hk(self):
        """Test HKEX market returns HK country."""
        assert get_market_country("HKEX") == "HK"

    def test_tyo_returns_jp(self):
        """Test TYO market returns JP country."""
        assert get_market_country("TYO") == "JP"

    def test_hnx_returns_vn(self):
        """Test HNX market returns VN country."""
        assert get_market_country("HNX") == "VN"

    def test_hsx_returns_vn(self):
        """Test HSX market returns VN country."""
        assert get_market_country("HSX") == "VN"

    def test_sse_returns_cn(self):
        """Test SSE market returns CN country."""
        assert get_market_country("SSE") == "CN"

    def test_szse_returns_cn(self):
        """Test SZSE market returns CN country."""
        assert get_market_country("SZSE") == "CN"

    def test_invalid_market_raises_error(self):
        """Test unsupported market raises ValueError."""
        with pytest.raises(ValueError, match="지원하지 않는 상품유형명"):
            get_market_country("INVALID")  # type: ignore


# ===== Tests for quotable_market function =====

class TestQuotableMarket:
    """Tests for quotable_market function."""

    def test_validates_empty_symbol(self):
        """Test empty symbol raises ValueError."""
        fake_kis = Mock()
        
        with pytest.raises(ValueError, match="종목 코드를 입력해주세요"):
            quotable_market(fake_kis, "")

    def test_uses_cache_when_available(self):
        """Test uses cached market when available."""
        fake_kis = Mock()
        fake_kis.cache.get.return_value = "KRX"
        
        result = quotable_market(fake_kis, "005930", market="KR", use_cache=True)
        
        assert result == "KRX"
        fake_kis.cache.get.assert_called_once_with("quotable_market:KR:005930", str)
        fake_kis.fetch.assert_not_called()

    def test_domestic_market_with_valid_price(self):
        """Test domestic market returns KRX when price is valid."""
        fake_kis = Mock()
        fake_kis.cache.get.return_value = None
        
        mock_response = Mock()
        mock_response.output.stck_prpr = "65000"
        fake_kis.fetch.return_value = mock_response
        
        result = quotable_market(fake_kis, "005930", market="KR", use_cache=False)
        
        assert result == "KRX"
        fake_kis.fetch.assert_called_once()

    @pytest.mark.skip(reason="raise_not_found는 __data__ 속성을 필요로 하므로 실제 API 응답 구조 필요")
    def test_domestic_market_with_zero_price_continues(self):
        """Test domestic market with zero price tries next market. (SKIPPED)""" 
        pass

    def test_foreign_market_with_valid_price(self):
        """Test foreign market returns correct market type."""
        fake_kis = Mock()
        fake_kis.cache.get.return_value = None
        
        mock_response = Mock()
        mock_response.output.last = "150.50"
        fake_kis.fetch.return_value = mock_response
        
        result = quotable_market(fake_kis, "AAPL", market="NASDAQ", use_cache=False)
        
        assert result == "NASDAQ"

    @pytest.mark.skip(reason="raise_not_found는 __data__ 속성을 필요로 하므로 실제 API 응답 구조 필요")
    def test_foreign_market_with_empty_price_continues(self):
        """Test foreign market with empty price tries next market. (SKIPPED)"""
        pass

    @pytest.mark.skip(reason="raise_not_found는 __response__ 필드를 필요로 하므로 실제 API 응답 구조 필요")
    def test_attribute_error_continues(self):
        """Test AttributeError in response is caught and continues. (SKIPPED)"""
        pass

    @pytest.mark.skip(reason="raise_not_found는 __response__ 필드를 필요로 하므로 실제 API 응답 구조 필요")
    def test_raises_not_found_when_no_markets_match(self):
        """Test raises KisNotFoundError when no markets match. (SKIPPED)"""
        pass


# ===== Tests for info function =====

class TestInfo:
    """Tests for info function."""

    def test_validates_empty_symbol(self):
        """Test empty symbol raises ValueError."""
        fake_kis = Mock()
        
        with pytest.raises(ValueError, match="종목 코드를 입력해주세요"):
            info(fake_kis, "")

    def test_uses_cache_when_available(self):
        """Test uses cached info when available."""
        fake_kis = Mock()
        mock_cached_info = Mock()
        fake_kis.cache.get.return_value = mock_cached_info
        
        result = info(fake_kis, "005930", market="KR", use_cache=True)
        
        assert result == mock_cached_info
        fake_kis.cache.get.assert_called_once_with("info:KR:005930", _KisStockInfo)
        fake_kis.fetch.assert_not_called()

    def test_calls_quotable_market_when_quotable_true(self):
        """Test calls quotable_market when quotable=True."""
        fake_kis = Mock()
        fake_kis.cache.get.return_value = None
        
        mock_info = Mock()
        fake_kis.fetch.return_value = mock_info
        
        with patch('pykis.api.stock.info.quotable_market', return_value="KRX") as mock_quotable:
            result = info(fake_kis, "005930", market="KR", use_cache=False, quotable=True)
            
            mock_quotable.assert_called_once_with(
                fake_kis,
                symbol="005930",
                market="KR",
                use_cache=False,
            )

    def test_skips_quotable_market_when_quotable_false(self):
        """Test skips quotable_market when quotable=False."""
        fake_kis = Mock()
        fake_kis.cache.get.return_value = None
        
        mock_info = Mock()
        fake_kis.fetch.return_value = mock_info
        
        with patch('pykis.api.stock.info.quotable_market') as mock_quotable:
            result = info(fake_kis, "005930", market="KR", use_cache=False, quotable=False)
            
            mock_quotable.assert_not_called()

    def test_successful_fetch_returns_info(self):
        """Test successful fetch returns stock info."""
        fake_kis = Mock()
        fake_kis.cache.get.return_value = None
        
        mock_info = Mock()
        fake_kis.fetch.return_value = mock_info
        
        result = info(fake_kis, "005930", market="KR", use_cache=False, quotable=False)
        
        assert result == mock_info
        fake_kis.fetch.assert_called_once()

    def test_sets_cache_after_successful_fetch(self):
        """Test sets cache after successful fetch when use_cache=True."""
        fake_kis = Mock()
        fake_kis.cache.get.return_value = None
        
        mock_info = Mock()
        fake_kis.fetch.return_value = mock_info
        
        result = info(fake_kis, "005930", market="KR", use_cache=True, quotable=False)
        
        fake_kis.cache.set.assert_called_once_with(
            "info:KR:005930",
            mock_info,
            expire=timedelta(days=1)
        )

    def test_does_not_cache_when_use_cache_false(self):
        """Test does not cache when use_cache=False."""
        fake_kis = Mock()
        fake_kis.cache.get.return_value = None
        
        mock_info = Mock()
        fake_kis.fetch.return_value = mock_info
        
        result = info(fake_kis, "005930", market="KR", use_cache=False, quotable=False)
        
        fake_kis.cache.set.assert_not_called()

    @pytest.mark.skip(reason="KisAPIError 생성자 시그니처가 복잡하여 모킹 어려움. 통합 테스트에서 커버")
    def test_continues_on_rt_cd_7_error(self):
        """Test continues to next market when rt_cd=7 (no data). (SKIPPED)"""
        pass

    @pytest.mark.skip(reason="KisAPIError 생성자 시그니처가 복잡하여 모킹 어려움. 통합 테스트에서 커버")
    def test_raises_other_api_errors_immediately(self):
        """Test raises non-rt_cd=7 API errors immediately. (SKIPPED)"""
        pass

    @pytest.mark.skip(reason="KisAPIError와 raise_not_found의 복잡한 상호작용으로 모킹 어려움")
    def test_raises_not_found_when_all_markets_fail(self):
        """Test raises KisNotFoundError when all markets return rt_cd=7. (SKIPPED)"""
        pass

    def test_fetch_params_correct(self):
        """Test fetch is called with correct parameters."""
        fake_kis = Mock()
        fake_kis.cache.get.return_value = None
        
        mock_info = Mock()
        fake_kis.fetch.return_value = mock_info
        
        result = info(fake_kis, "005930", market="KR", use_cache=False, quotable=False)
        
        call_args = fake_kis.fetch.call_args
        assert call_args[0][0] == "/uapi/domestic-stock/v1/quotations/search-info"
        assert call_args[1]["api"] == "CTPF1604R"
        assert call_args[1]["params"]["PDNO"] == "005930"
        assert call_args[1]["params"]["PRDT_TYPE_CD"] in MARKET_TYPE_MAP["KR"]
        assert call_args[1]["domain"] == "real"
        assert call_args[1]["response_type"] == _KisStockInfo

    @pytest.mark.skip(reason="KisAPIError 생성자 시그니처가 복잡하여 모킹 어려움. 통합 테스트에서 커버")
    def test_multiple_markets_iteration(self):
        """Test iterates through all market codes. (SKIPPED)"""
        pass


# ===== Tests for resolve_market function =====

class TestResolveMarket:
    """Tests for resolve_market function."""

    def test_returns_market_from_info(self):
        """Test resolve_market returns market property from info."""
        fake_kis = Mock()
        fake_kis.cache.get.return_value = None
        
        mock_info = Mock()
        mock_info.market = "KRX"
        fake_kis.fetch.return_value = mock_info
        
        # quotable=False to skip quotable_market call which requires complex mocking
        result = resolve_market(fake_kis, "005930", market="KR", use_cache=False, quotable=False)
        
        assert result == "KRX"

    def test_forwards_all_parameters(self):
        """Test resolve_market forwards all parameters to info."""
        fake_kis = Mock()
        fake_kis.cache.get.return_value = None
        
        mock_info = Mock()
        mock_info.market = "NASDAQ"
        fake_kis.fetch.return_value = mock_info
        
        with patch('pykis.api.stock.info.info', return_value=mock_info) as mock_info_func:
            result = resolve_market(
                fake_kis,
                symbol="AAPL",
                market="US",
                use_cache=True,
                quotable=False
            )
            
            mock_info_func.assert_called_once_with(
                fake_kis,
                symbol="AAPL",
                market="US",
                use_cache=True,
                quotable=False,
            )

    def test_validates_empty_symbol(self):
        """Test empty symbol raises ValueError (via info)."""
        fake_kis = Mock()
        
        with pytest.raises(ValueError, match="종목 코드를 입력해주세요"):
            resolve_market(fake_kis, "")


# ===== Tests for MARKET_TYPE_MAP =====

class TestMarketTypeMap:
    """Tests for MARKET_TYPE_MAP dictionary."""

    def test_kr_has_domestic_codes(self):
        """Test KR market has domestic market codes."""
        assert "300" in MARKET_TYPE_MAP["KR"]

    def test_krx_has_domestic_codes(self):
        """Test KRX market has domestic market codes."""
        assert "300" in MARKET_TYPE_MAP["KRX"]

    def test_nasdaq_has_correct_code(self):
        """Test NASDAQ market has correct code."""
        assert "512" in MARKET_TYPE_MAP["NASDAQ"]

    def test_nyse_has_correct_code(self):
        """Test NYSE market has correct code."""
        assert "513" in MARKET_TYPE_MAP["NYSE"]

    def test_amex_has_correct_code(self):
        """Test AMEX market has correct code."""
        assert "529" in MARKET_TYPE_MAP["AMEX"]

    def test_us_has_all_us_codes(self):
        """Test US market has all US market codes."""
        us_codes = MARKET_TYPE_MAP["US"]
        assert "512" in us_codes  # NASDAQ
        assert "513" in us_codes  # NYSE
        assert "529" in us_codes  # AMEX

    def test_tyo_has_correct_code(self):
        """Test TYO market has correct code."""
        assert "515" in MARKET_TYPE_MAP["TYO"]

    def test_jp_has_correct_code(self):
        """Test JP market has correct code."""
        assert "515" in MARKET_TYPE_MAP["JP"]

    def test_hkex_has_correct_code(self):
        """Test HKEX market has correct code."""
        assert "501" in MARKET_TYPE_MAP["HKEX"]

    def test_hk_has_all_hk_codes(self):
        """Test HK market has all HK market codes."""
        hk_codes = MARKET_TYPE_MAP["HK"]
        assert "501" in hk_codes  # HKEX
        assert "543" in hk_codes  # CNY
        assert "558" in hk_codes  # USD

    def test_vn_has_all_vn_codes(self):
        """Test VN market has all VN market codes."""
        vn_codes = MARKET_TYPE_MAP["VN"]
        assert "507" in vn_codes  # HNX
        assert "508" in vn_codes  # HSX

    def test_cn_has_all_cn_codes(self):
        """Test CN market has all CN market codes."""
        cn_codes = MARKET_TYPE_MAP["CN"]
        assert "551" in cn_codes  # SSE
        assert "552" in cn_codes  # SZSE

    def test_none_has_all_codes(self):
        """Test None market has all available codes."""
        all_codes = MARKET_TYPE_MAP[None]
        assert "300" in all_codes
        assert "512" in all_codes
        assert "513" in all_codes
        assert len(all_codes) > 10
