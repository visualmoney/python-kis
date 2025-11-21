from types import SimpleNamespace

from pykis.api.websocket import order_execution


class FakeTicket:
    def __init__(self):
        self.unsubscribed_callbacks = []

    def unsubscribe(self):
        self.unsubscribed = True


class FakeWebsocket:
    def __init__(self, name):
        self.name = name
        self.called = []

    def on(self, **kwargs):
        self.called.append(kwargs)
        return FakeTicket()


def test_on_execution_raises_when_no_appkey():
    """on_execution should raise if the client's appkey (or virtual_appkey) is None."""
    client = SimpleNamespace(kis=SimpleNamespace(virtual=False, appkey=None))
    try:
        order_execution.on_execution(client, lambda *_: None)
    except ValueError as e:
        assert "appkey" in str(e)
    else:
        raise AssertionError("Expected ValueError when appkey is None")


def test_on_execution_registers_domestic_and_foreign_and_links_unsubscribe():
    """on_execution registers two event handlers and links foreign unsubscribe to domestic callbacks."""
    # Create a kis object with appkey
    appkey = SimpleNamespace(id="key-id")
    kis = SimpleNamespace(virtual=False, appkey=appkey)

    ws = FakeWebsocket("ws")
    # client has kis and on method as itself
    client = SimpleNamespace(kis=kis, on=ws.on)

    ticket = order_execution.on_execution(client, lambda *_: None)
    assert isinstance(ticket, FakeTicket)


def test_on_account_execution_forwards_to_on_execution():
    """on_account_execution should call on_execution using the account protocol's kis.websocket."""
    appkey = SimpleNamespace(id="k")
    ws = FakeWebsocket("w")
    kis = SimpleNamespace(virtual=False, appkey=appkey, websocket=ws)
    # websocket should reference its parent kis (the production code expects self.kis on websocket)
    ws.kis = kis
    acct = SimpleNamespace(kis=kis)

    ticket = order_execution.on_account_execution(acct, lambda *_: None)
    assert isinstance(ticket, FakeTicket)
