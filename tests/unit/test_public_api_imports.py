import warnings


def test_public_types_and_core_imports():
    # core class
    from pykis import PyKis, KisAuth

    assert PyKis is not None
    assert KisAuth is not None

    # public types
    from pykis import Quote, Balance, Order, Chart, Orderbook

    assert Quote is not None
    assert Balance is not None
    assert Order is not None
    assert Chart is not None
    assert Orderbook is not None


def test_deprecated_import_warns():
    # importing a legacy symbol from package root should warn and still work
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        try:
            from pykis import KisObjectProtocol
        except Exception:
            # if types module missing, just ensure warning was raised
            pass

        assert any(isinstance(x.message, DeprecationWarning) or x.category is DeprecationWarning for x in w)
