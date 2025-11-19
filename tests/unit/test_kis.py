import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, mock_open, patch

import pytest

from pykis.api.auth.token import KisAccessToken
from pykis.client.auth import KisAuth
from pykis.client.exceptions import KisHTTPError
from pykis.kis import PyKis


@pytest.fixture
def mock_kis_auth():
    """KisAuth 객체를 모킹합니다."""
    auth = MagicMock(spec=KisAuth)
    auth.virtual = False
    auth.id = "test_id"
    auth.key = MagicMock()
    auth.key.id = "test_id"
    auth.key.appkey = "test_appkey_36chars_long_1234567890"
    auth.key.secretkey = "test_secretkey"
    auth.account_number = "12345678-01"
    return auth


@pytest.fixture
def mock_virtual_kis_auth():
    """가상 KisAuth 객체를 모킹합니다."""
    auth = MagicMock(spec=KisAuth)
    auth.virtual = True
    auth.id = "v_test_id"
    auth.key = MagicMock()
    auth.key.id = "v_test_id"
    auth.key.appkey = "v_test_appkey"
    auth.key.secretkey = "v_test_secretkey"
    auth.account_number = "V12345678-01"
    return auth


@patch("pykis.kis.KisAuth.load")
def test_init_with_auth_path(mock_load_auth, mock_kis_auth):
    """auth 파일 경로로 PyKis 초기화 테스트"""
    mock_load_auth.return_value = mock_kis_auth
    kis = PyKis("fake/path/auth.json", use_websocket=False)
    mock_load_auth.assert_called_once_with("fake/path/auth.json")
    assert kis.appkey == mock_kis_auth.key
    assert str(kis.primary_account) == mock_kis_auth.account_number
    assert not kis.virtual


def test_init_with_kwargs():
    """키워드 인자로 PyKis 초기화 테스트"""
    kis = PyKis(
        id="test_id",
        appkey="test_appkey_36chars_1234567890_abcde",
        secretkey="test_secretkey_180chars_long_aa72vEu5ejiqRwpPRetP2fPdMVeTswa2oitr48MiH1Orje0W8sflP9s9cOfottRWfGsxetpntEpxNo+6zNSZsKUo7G7f8COnXdouYtdUsi34nMVMzDoPrbN5Uu2podrHD8Bhh0zWVHW8nCXu2kEojo=",
        account="12345678-01",
        use_websocket=False,
    )
    assert kis.appkey.id == "test_id"
    assert kis.appkey.appkey == "test_appkey_36chars_1234567890_abcde"
    assert str(kis.primary_account) == "12345678-01"
    assert not kis.virtual


# def test_init_with_virtual_kwargs():
#     """가상 계좌 키워드 인자로 PyKis 초기화 테스트"""
#     kis = PyKis(
#         id="test_id",
#         appkey="test_appkey",
#         secretkey="test_secretkey",
#         virtual_id="v_test_id",
#         virtual_appkey="v_test_appkey",
#         virtual_secretkey="v_test_secretkey",
#         account="V12345678-01",
#         use_websocket=False,
#     )
#     assert kis.virtual_appkey is not None
#     assert kis.virtual_appkey.id == "v_test_id"
#     assert kis.virtual_appkey.appkey == "v_test_appkey"
#     assert kis.primary_account.account == "V12345678-01"
#     assert kis.virtual


# def test_init_value_errors():
#     """초기화 시 발생하는 ValueError 테스트"""
#     with pytest.raises(ValueError, match="id를 입력해야 합니다."):
#         PyKis(use_websocket=False)
#     with pytest.raises(ValueError, match="appkey를 입력해야 합니다."):
#         PyKis(id="test", use_websocket=False)
#     with pytest.raises(ValueError, match="secretkey를 입력해야 합니다."):
#         PyKis(id="test", appkey="key", use_websocket=False)
#     with pytest.raises(ValueError, match="virtual_id를 입력해야 합니다."):
#         PyKis(
#             id="t",
#             appkey="k",
#             secretkey="s",
#             virtual_appkey="vk",
#             virtual_secretkey="vs",
#             use_websocket=False,
#         )


# @patch("pykis.kis.requests.Session")
# @patch("pykis.api.auth.token.token_issue")
# def test_token_property(mock_token_issue, mock_session):
#     """token 속성 테스트 (만료 및 재발급)"""
#     kis = PyKis(id="t", appkey="k", secretkey="s", use_websocket=False)

#     # 토큰이 없을 때 발급
#     mock_token_issue.return_value = KisAccessToken(
#         access_token="new_token", token_type="Bearer", expires_in=86400
#     )
#     assert kis.token.token == "new_token"
#     mock_token_issue.assert_called_once_with(kis, domain="real")

#     # 토큰이 유효할 때 재사용
#     mock_token_issue.reset_mock()
#     assert kis.token.token == "new_token"
#     mock_token_issue.assert_not_called()

#     # 토큰이 만료되었을 때 재발급
#     kis._token.expires_at = datetime.now() - timedelta(minutes=1)
#     mock_token_issue.return_value = KisAccessToken(
#         access_token="refreshed_token", token_type="Bearer", expires_in=86400
#     )
#     assert kis.token.token == "refreshed_token"
#     mock_token_issue.assert_called_once_with(kis, domain="real")


# @patch("pykis.kis.requests.Session")
# def test_request_rate_limit_and_token_expiry(mock_session):
#     """API 요청 시 Rate Limit 및 토큰 만료 처리 테스트"""
#     kis = PyKis(id="t", appkey="k", secretkey="s", use_websocket=False)
#     kis.token = KisAccessToken(access_token="test_token", token_type="Bearer", expires_in=86400)

#     mock_request = mock_session.return_value.request
#     # 1. Rate limit, 2. Token expired, 3. Success
#     mock_request.side_effect = [
#         MagicMock(ok=False, json=lambda: {"msg_cd": "EGW00201"}),
#         MagicMock(ok=False, json=lambda: {"msg_cd": "EGW00123"}),
#         MagicMock(ok=True, json=lambda: {"rt_cd": "0"}),
#     ]

#     with patch("pykis.api.auth.token.token_issue") as mock_token_issue:
#         mock_token_issue.return_value = KisAccessToken(
#             access_token="new_token", token_type="Bearer", expires_in=86400
#         )

#         with patch("pykis.kis.sleep") as mock_sleep:
#             response = kis.request("/")

#             assert response.json()["rt_cd"] == "0"
#             assert mock_request.call_count == 3
#             mock_sleep.assert_called_once_with(0.1)  # Rate limit 대기
#             mock_token_issue.assert_called_once()  # 토큰 재발급
#             assert kis.token.token == "new_token"


# @patch("pykis.kis.requests.Session")
# def test_request_http_error(mock_session):
#     """HTTP 에러 발생 테스트"""
#     kis = PyKis(id="t", appkey="k", secretkey="s", use_websocket=False)
#     kis.token = KisAccessToken(access_token="test_token", token_type="Bearer", expires_in=86400)

#     mock_response = MagicMock(ok=False, status_code=500)
#     mock_response.json.return_value = {"msg_cd": "SOME_ERROR", "msg1": "Error message"}
#     mock_session.return_value.request.return_value = mock_response

#     with pytest.raises(KisHTTPError):
#         kis.request("/")


# @patch("pykis.kis.Path.exists", return_value=True)
# @patch("pykis.kis.KisAccessToken.load")
# @patch("builtins.open", new_callable=mock_open)
# def test_load_cached_token(mock_file, mock_load_token, mock_exists):
#     """캐시된 토큰 로딩 테스트"""
#     mock_token = KisAccessToken(access_token="cached_token", token_type="Bearer", expires_in=86400)
#     mock_load_token.return_value = mock_token

#     kis = PyKis(id="t", appkey="k", secretkey="s", keep_token=True, use_websocket=False)

#     assert kis._token == mock_token
#     assert mock_load_token.call_count == 1


# @patch("pykis.kis.Path.mkdir")
# @patch("pykis.kis.KisAccessToken.save")
# def test_save_cached_token(mock_save, mock_mkdir):
#     """토큰 캐시 저장 테스트"""
#     kis = PyKis(id="t", appkey="k", secretkey="s", keep_token=True, use_websocket=False)
#     token = KisAccessToken(access_token="new_token", token_type="Bearer", expires_in=86400)
#     kis._token = token

#     with patch("pykis.kis.PyKis._get_hashed_token_name") as mock_hash_name:
#         mock_hash_name.return_value = "hashed_token_name.json"
#         kis._save_cached_token(kis._keep_token, domain="real")

#         mock_save.assert_called_once()
#         # `token.save`가 올바른 경로와 함께 호출되었는지 확인
#         saved_path = mock_save.call_args[0][0]
#         assert saved_path.name == "hashed_token_name.json"
