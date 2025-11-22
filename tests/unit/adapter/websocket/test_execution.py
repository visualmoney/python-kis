"""Unit tests for pykis.adapter.websocket.execution"""
from types import SimpleNamespace


def test_realtime_orderable_account_mixin_on_execution():
    """KisRealtimeOrderableAccountMixin.on should forward to on_account_execution."""
    from pykis.adapter.websocket.execution import KisRealtimeOrderableAccountMixin
    
    calls = []
    
    def fake_on_account_execution(self, callback, where=None, once=False):
        calls.append(("on_account_execution", callback, where, once))
        return "ticket"
    
    class TestAccount(KisRealtimeOrderableAccountMixin):
        pass
    
    import pykis.api.websocket.order_execution as exec_api
    original = exec_api.on_account_execution
    exec_api.on_account_execution = fake_on_account_execution
    
    try:
        acct = TestAccount()
        cb = lambda *_: None
        ticket = acct.on("execution", cb, where=None, once=False)
        assert ticket == "ticket"
        assert calls[0][0] == "on_account_execution"
        assert calls[0][3] is False  # once=False
    finally:
        exec_api.on_account_execution = original


def test_realtime_orderable_account_mixin_once_execution():
    """KisRealtimeOrderableAccountMixin.once should call with once=True."""
    from pykis.adapter.websocket.execution import KisRealtimeOrderableAccountMixin
    
    calls = []
    
    def fake_on_account_execution(self, callback, where=None, once=False):
        calls.append(("on_account_execution", once))
        return "ticket"
    
    class TestAccount(KisRealtimeOrderableAccountMixin):
        pass
    
    import pykis.api.websocket.order_execution as exec_api
    original = exec_api.on_account_execution
    exec_api.on_account_execution = fake_on_account_execution
    
    try:
        acct = TestAccount()
        ticket = acct.once("execution", lambda *_: None)
        assert ticket == "ticket"
        assert calls[0][1] is True  # once=True
    finally:
        exec_api.on_account_execution = original


def test_account_mixin_raises_for_unknown_event():
    """Mixin should raise ValueError for unknown event types."""
    from pykis.adapter.websocket.execution import KisRealtimeOrderableAccountMixin
    
    class TestAccount(KisRealtimeOrderableAccountMixin):
        pass
    
    acct = TestAccount()
    
    try:
        acct.on("unknown_event", lambda *_: None)
    except ValueError as e:
        assert "Unknown event" in str(e)
    else:
        raise AssertionError("Expected ValueError for unknown event")


def test_realtime_orderable_order_mixin_wraps_filter():
    """KisRealtimeOrderableOrderMixin.on should wrap filter with KisMultiEventFilter."""
    from pykis.adapter.websocket.execution import KisRealtimeOrderableOrderMixin
    
    calls = []
    
    def fake_on_account_execution(self, callback, where=None, once=False):
        calls.append(("on", where, once))
        return "ticket"
    
    class TestOrder(KisRealtimeOrderableOrderMixin):
        pass
    
    import pykis.api.websocket.order_execution as exec_api
    original = exec_api.on_account_execution
    exec_api.on_account_execution = fake_on_account_execution
    
    try:
        order = TestOrder()
        fake_filter = SimpleNamespace(name="filter")
        
        # with where filter -> should wrap with KisMultiEventFilter
        ticket = order.on("execution", lambda *_: None, where=fake_filter, once=False)
        assert ticket == "ticket"
        assert calls[0][2] is False
        
        # without where -> should use self as filter
        ticket2 = order.on("execution", lambda *_: None, where=None, once=True)
        assert calls[1][1] is order
        assert calls[1][2] is True
    finally:
        exec_api.on_account_execution = original


def test_order_mixin_once_sets_once_true():
    """KisRealtimeOrderableOrderMixin.once should set once=True."""
    from pykis.adapter.websocket.execution import KisRealtimeOrderableOrderMixin
    
    calls = []
    
    def fake_on_account_execution(self, callback, where=None, once=False):
        calls.append(("once", once))
        return "ticket"
    
    class TestOrder(KisRealtimeOrderableOrderMixin):
        pass
    
    import pykis.api.websocket.order_execution as exec_api
    original = exec_api.on_account_execution
    exec_api.on_account_execution = fake_on_account_execution
    
    try:
        order = TestOrder()
        ticket = order.once("execution", lambda *_: None)
        assert ticket == "ticket"
        assert calls[0][1] is True
    finally:
        exec_api.on_account_execution = original
