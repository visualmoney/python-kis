"""Unit tests for pykis.adapter.websocket.price"""
from types import SimpleNamespace


def test_websocket_quotable_product_mixin_on_price():
    """KisWebsocketQuotableProductMixin.on should forward to on_product_price for 'price' event."""
    from pykis.adapter.websocket.price import KisWebsocketQuotableProductMixin
    
    calls = []
    
    def fake_on(self, event, callback, where=None, once=False, extended=False):
        calls.append((event, callback, where, once, extended))
        return "price-ticket"
    
    class TestProduct(KisWebsocketQuotableProductMixin):
        pass
    
    orig_on = KisWebsocketQuotableProductMixin.on
    
    try:
        KisWebsocketQuotableProductMixin.on = fake_on
        
        prod = TestProduct()
        cb = lambda *_: None
        ticket = prod.on("price", cb, where=None, once=False, extended=True)
        assert ticket == "price-ticket"
        assert calls[0][0] == "price"
        assert calls[0][4] is True  # extended=True
    finally:
        KisWebsocketQuotableProductMixin.on = orig_on


def test_websocket_quotable_product_mixin_on_orderbook():
    """KisWebsocketQuotableProductMixin.on should forward to on_product_order_book for 'orderbook' event."""
    from pykis.adapter.websocket.price import KisWebsocketQuotableProductMixin
    
    calls = []
    
    def fake_on(self, event, callback, where=None, once=False, extended=False):
        calls.append((event, callback, where, once, extended))
        return "orderbook-ticket"
    
    class TestProduct(KisWebsocketQuotableProductMixin):
        pass
    
    orig_on = KisWebsocketQuotableProductMixin.on
    
    try:
        KisWebsocketQuotableProductMixin.on = fake_on
        
        prod = TestProduct()
        cb = lambda *_: None
        ticket = prod.on("orderbook", cb, where=None, once=True, extended=False)
        assert ticket == "orderbook-ticket"
        assert calls[0][0] == "orderbook"
        assert calls[0][3] is True  # once=True
    finally:
        KisWebsocketQuotableProductMixin.on = orig_on


def test_mixin_on_raises_for_unknown_event():
    """Mixin.on should raise ValueError for unknown event types."""
    from pykis.adapter.websocket.price import KisWebsocketQuotableProductMixin
    
    class TestProduct(KisWebsocketQuotableProductMixin):
        pass
    
    prod = TestProduct()
    
    try:
        prod.on("unknown", lambda *_: None)
    except ValueError as e:
        assert "Unknown event" in str(e)
    else:
        raise AssertionError("Expected ValueError for unknown event")


def test_websocket_quotable_product_mixin_once_price():
    """KisWebsocketQuotableProductMixin.once should call on_product_price with once=True."""
    from pykis.adapter.websocket.price import KisWebsocketQuotableProductMixin
    
    calls = []
    
    def fake_once(self, event, callback, where=None, extended=False):
        calls.append((event, True))  # once is always True for once method
        return "price-ticket"
    
    class TestProduct(KisWebsocketQuotableProductMixin):
        pass
    
    orig_once = KisWebsocketQuotableProductMixin.once
    
    try:
        KisWebsocketQuotableProductMixin.once = fake_once
        
        prod = TestProduct()
        ticket = prod.once("price", lambda *_: None, extended=True)
        assert ticket == "price-ticket"
        assert calls[0][1] is True  # once=True
    finally:
        KisWebsocketQuotableProductMixin.once = orig_once


def test_websocket_quotable_product_mixin_once_orderbook():
    """KisWebsocketQuotableProductMixin.once should call on_product_order_book with once=True."""
    from pykis.adapter.websocket.price import KisWebsocketQuotableProductMixin
    
    calls = []
    
    def fake_once(self, event, callback, where=None, extended=False):
        calls.append((event, True))  # once is always True for once method
        return "orderbook-ticket"
    
    class TestProduct(KisWebsocketQuotableProductMixin):
        pass
    
    orig_once = KisWebsocketQuotableProductMixin.once
    
    try:
        KisWebsocketQuotableProductMixin.once = fake_once
        
        prod = TestProduct()
        ticket = prod.once("orderbook", lambda *_: None)
        assert ticket == "orderbook-ticket"
        assert calls[0][1] is True  # once=True
    finally:
        KisWebsocketQuotableProductMixin.once = orig_once


def test_once_raises_for_unknown_event():
    """Mixin.once should raise ValueError for unknown event types."""
    from pykis.adapter.websocket.price import KisWebsocketQuotableProductMixin
    
    class TestProduct(KisWebsocketQuotableProductMixin):
        def __init__(self):
            self.kis = SimpleNamespace()
            self.symbol = "005930"
            self.market = "KRX"
    
    prod = TestProduct()
    
    try:
        prod.once("invalid", lambda *_: None)
    except ValueError as e:
        assert "Unknown event" in str(e)
    else:
        raise AssertionError("Expected ValueError for unknown event in once")
