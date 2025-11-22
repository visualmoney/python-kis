import base64
import json

import pytest

from types import SimpleNamespace

import pykis.client.websocket as websocket_mod
from pykis.client.websocket import (
    KisWebsocketClient,
    KisWebsocketTR,
    TR_SUBSCRIBE_TYPE,
    TR_UNSUBSCRIBE_TYPE,
)


class DummyKis:
    def __init__(self, virtual=False):
        self.virtual = virtual


class DummyWS:
    def __init__(self):
        self.sent = []

    def send(self, data):
        self.sent.append(data)


def make_client(monkeypatch, virtual=False):
    kis = DummyKis(virtual=virtual)
    c = KisWebsocketClient(kis=kis, virtual=False)
    # prevent threads from being started by connect
    c.thread = None
    # provide a fake websocket approval key function so KisWebsocketRequest.build() works
    monkeypatch.setattr(
        "pykis.api.auth.websocket.websocket_approval_key",
        lambda kis_obj, domain=None: SimpleNamespace(approval_key="APPKEY-123"),
    )
    return c


def test_subscribe_and_unsubscribe_sends_requests(monkeypatch):
    c = make_client(monkeypatch)
    ws = DummyWS()
    c.websocket = ws
    c._connected_event.set()

    c.subscribe("ID1", "K1")
    assert KisWebsocketTR("ID1", "K1") in c._subscriptions
    # last sent message should be a JSON with header tr_type TR_SUBSCRIBE_TYPE
    assert ws.sent, "no message sent"
    sent = json.loads(ws.sent[-1])
    assert sent["header"]["tr_type"] == TR_SUBSCRIBE_TYPE

    c.unsubscribe("ID1", "K1")
    assert KisWebsocketTR("ID1", "K1") not in c._subscriptions
    # unsubscribe message sent
    assert json.loads(ws.sent[-1])["header"]["tr_type"] == TR_UNSUBSCRIBE_TYPE


def test_subscribe_max_limit_raises(monkeypatch):
    c = make_client(monkeypatch)
    # set max small for test
    monkeypatch.setattr(websocket_mod, "WEBSOCKET_MAX_SUBSCRIPTIONS", 1)
    ws = DummyWS()
    c.websocket = ws
    c._connected_event.set()

    c.subscribe("A", "")
    with pytest.raises(ValueError):
        c.subscribe("B", "")


def test_release_reference_unsubscribe_called(monkeypatch):
    c = make_client(monkeypatch)
    ws = DummyWS()
    c.websocket = ws
    c._connected_event.set()

    c.subscribe("X", "Y")
    # simulate reference release
    c._release_reference("X:Y", 0)
    # after release unsubscribe called, subscription removed
    assert KisWebsocketTR("X", "Y") not in c._subscriptions


def test_set_encryption_key_special_ids_get_empty_key(monkeypatch):
    c = make_client(monkeypatch)
    tr = KisWebsocketTR("H0STCNI0", "SOME")
    body = {"key": "kkey", "iv": "iivv"}
    c._set_encryption_key(tr, body)
    # key stored under tr with empty key
    stored = list(c._keychain.keys())[0]
    assert stored.key == ""
    assert isinstance(list(c._keychain.values())[0].key, bytes)


def test_handle_control_pingpong_and_subscribed_and_unsubscribed(monkeypatch):
    c = make_client(monkeypatch)
    ws = DummyWS()
    c.websocket = ws

    # PINGPONG echoes
    data = {"header": {"tr_id": "PINGPONG"}}
    assert c._handle_control(data) is None
    assert ws.sent
    sent = json.loads(ws.sent[-1])
    assert sent["header"]["tr_id"] == "PINGPONG"

    # subscribed
    ws.sent.clear()
    data2 = {"header": {"tr_id": "T1", "tr_key": "K"}, "body": {"msg_cd": "OPSP0000", "msg1": "ok"}}
    c._handle_control(data2)
    assert KisWebsocketTR("T1", "K") in c._registered_subscriptions

    # unsubscribed
    data3 = {"header": {"tr_id": "T2"}, "body": {"msg_cd": "OPSP0001", "msg1": "ok"}}
    # add to registered to allow removal
    c._registered_subscriptions.add(KisWebsocketTR("T2", ""))
    c._handle_control(data3)
    assert KisWebsocketTR("T2", "") not in c._registered_subscriptions


def test_handle_event_early_returns(monkeypatch):
    c = make_client(monkeypatch)
    # case: encrypted but no key -> should return without exception
    msg = "1|NOKEY|1|AAA"
    c._keychain.clear()
    # no response mapping
    monkeypatch.setitem(websocket_mod.WEBSOCKET_RESPONSES_MAP, "NOKEY", None)
    c._handle_event(msg)

    # case: not encrypted and no mapping
    msg2 = "0|NOMAP|1|{}"
    # ensure mapping has no entry
    websocket_mod.WEBSOCKET_RESPONSES_MAP.pop("NOMAP", None)
    c._handle_event(msg2)


def test_ensure_primary_client_creates_and_returns_primary(monkeypatch):
    kis = DummyKis(virtual=True)
    c = KisWebsocketClient(kis=kis, virtual=False)
    primary = c._ensure_primary_client()
    assert primary is not c
    assert c._primary_client is primary


def test_request_true_and_false(monkeypatch):
    c = make_client(monkeypatch)
    # no websocket -> False
    c.websocket = None
    assert c._request("X") is False

    # websocket present but not connected -> False
    c.websocket = DummyWS()
    c._connected_event.clear()
    assert c._request("X") is False

    # connected -> send returns True
    c._connected_event.set()
    c.websocket = DummyWS()
    assert c._request("X") is True


def test_reset_session_state_and_restore_subscriptions(monkeypatch):
    c = make_client(monkeypatch)
    # populate registered and keychain
    c._registered_subscriptions.add(KisWebsocketTR("A", ""))
    c._keychain[KisWebsocketTR("B", "")] = object()

    c._reset_session_state()
    assert not c._registered_subscriptions
    assert not c._keychain

    # restore subscriptions calls _request for each missing registered
    # put one subscription not in registered
    c._subscriptions.add(KisWebsocketTR("R", ""))
    called = []

    def fake_request(t, body=None, force=False):
        called.append((t, body, force))

    monkeypatch.setattr(c, "_request", fake_request)
    c._restore_subscriptions()
    assert called and called[0][2] is True


def test_run_forever_acquire_failure_and_on_open_on_close_on_error(monkeypatch):
    c = make_client(monkeypatch)
    # make connect_lock's acquire return False
    class LockLike:
        def acquire(self, block=False):
            return False

    c._connect_lock = LockLike()
    assert c._run_forever() is False

    # test on_open sets connected event and calls reset/restore
    invoked = {"reset": False, "restore": False}
    monkeypatch.setattr(c, "_reset_session_state", lambda: invoked.update({"reset": True}))
    monkeypatch.setattr(c, "_restore_subscriptions", lambda: invoked.update({"restore": True}))
    ws = object()
    c.websocket = ws
    c._on_open(ws)
    assert invoked["reset"] and invoked["restore"]
    assert c._connected_event.is_set()

    # on_error should handle different types without raising
    c._on_error(ws, Exception("boom"))
    from websocket import WebSocketConnectionClosedException

    c._on_error(ws, WebSocketConnectionClosedException())
    c._on_error(ws, KeyboardInterrupt())

    # on_close should not raise
    c._on_close(ws, 1000, "bye")


def test_on_message_routes(monkeypatch):
    c = make_client(monkeypatch)
    # patch handlers
    called = {"event": False, "control": False}
    monkeypatch.setattr(c, "_handle_event", lambda m: called.update({"event": True}))
    monkeypatch.setattr(c, "_handle_control", lambda d: called.update({"control": True}))

    # event message
    c.websocket = object()
    c._on_message(c.websocket, "0|X|1|{}")
    assert called["event"]

    # control message
    called["event"] = False
    c._on_message(c.websocket, json.dumps({}))
    assert called["control"]


def test_set_encryption_key_non_special_and_handle_event_decryption(monkeypatch):
    c = make_client(monkeypatch)
    # non-special id retains key
    tr = KisWebsocketTR("NORMAL", "K")
    body = {"key": "k" * 16, "iv": "i" * 16}
    c._set_encryption_key(tr, body)
    assert KisWebsocketTR("NORMAL", "K") in c._keychain

    # prepare key to encrypt a small payload
    ek = c._keychain[KisWebsocketTR("NORMAL", "K")]
    plaintext = b"{}\n"
    # pad and encrypt using class cipher
    from cryptography.hazmat.primitives import padding as _padding
    from cryptography.hazmat.primitives.ciphers import algorithms as _algorithms
    padder = _padding.PKCS7(_algorithms.AES.block_size).padder()
    padded = padder.update(plaintext) + padder.finalize()
    encryptor = ek.cipher.encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()

    # ensure WEBSOCKET_RESPONSES_MAP has mapping for NORMAL
    monkeypatch.setitem(websocket_mod.WEBSOCKET_RESPONSES_MAP, "NORMAL", object())

    # monkeypatch KisWebsocketResponse.parse to a dummy that yields nothing
    from pykis.responses.websocket import KisWebsocketResponse
    monkeypatch.setattr(KisWebsocketResponse, "parse", staticmethod(lambda body, count, response_type: []))

    # event with encrypted flag
    msg = "1|NORMAL|1|" + base64.b64encode(ciphertext).decode("ascii")
    # should not raise
    c._handle_event(msg)

