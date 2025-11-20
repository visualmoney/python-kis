import builtins
from datetime import date, datetime, time
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from pykis.utils import repr as kisrepr


def test_decimal_datetime_date_time_zoneinfo_custom_reprs():
    # Decimal
    d = Decimal("2.5000")
    assert kisrepr._repr(d) == "2.5"

    # datetime -> repr(isoformat())
    dt = datetime(2020, 1, 2, 3, 4, 5)
    assert kisrepr._repr(dt) == repr(dt.isoformat())

    # date -> repr(isoformat())
    dd = date(2021, 12, 31)
    assert kisrepr._repr(dd) == repr(dd.isoformat())

    # time -> repr(isoformat())
    tt = time(12, 34, 56)
    assert kisrepr._repr(tt) == repr(tt.isoformat())

    # ZoneInfo -> ZoneInfo(key)
    z = ZoneInfo("UTC")
    assert kisrepr._repr(z) == f"{ZoneInfo.__name__}('UTC')"


def test_iterable_single_and_multiple_lines_and_ellipsis():
    # small list -> single line
    assert kisrepr.list_repr([1, 2, 3]) == "[1, 2, 3]"

    # small tuple -> single line
    assert kisrepr.tuple_repr((1,)) == "(1,)".replace(",)", ")") or kisrepr.tuple_repr((1,)) == "(1,)"  # tolerate tuple formatting

    # long list -> multiple lines
    big = list(range(10))
    out = kisrepr.list_repr(big, lines=None, ellipsis=None)
    assert "\n" in out

    # ellipsis cuts items and appends ', ...'
    out2 = kisrepr.list_repr(range(10), lines="single", ellipsis=3)
    assert out2.startswith("[")
    assert "..." in out2

    # set representation shouldn't raise and should contain elements
    s = {1, 2}
    sr = kisrepr.set_repr(s)
    assert sr.startswith("{")
    assert ("1" in sr) and ("2" in sr)


def test_iterable_invalid_tie_raises_value_error():
    # call internal _iterable_repr with odd-length tie to trigger ValueError
    with pytest.raises(ValueError):
        kisrepr._iterable_repr([1, 2], tie="{")


def test_dict_repr_single_and_multiple_and_depth_cutoff():
    # small dict -> single line
    d = {"a": 1, "b": 2}
    out = kisrepr.dict_repr(d)
    assert out.startswith("{") and ":" in out
    # nested dict with newline in value forces multiple
    d2 = {"a": "short", "b": "multi\nline"}
    out2 = kisrepr.dict_repr(d2)
    assert "\n" in out2

    # depth cutoff for dict
    assert kisrepr.dict_repr({"x": 1}, _depth=5, max_depth=0) == "{:...}"


def test_object_repr_single_multiple_unbounded_and_depth_cutoff():
    class WithAttr:
        a = 1

        @property
        def b(self):
            raise AttributeError("no b")

    inst = WithAttr()
    # specify fields to control order and include property that raises AttributeError
    out_single = kisrepr.object_repr(inst, fields=["a", "b"], lines="single")
    assert "WithAttr(" in out_single and "a=1" in out_single and "b=Unbounded" in out_single

    out_multi = kisrepr.object_repr(inst, fields=["a", "b"], lines="multiple")
    assert "WithAttr(" in out_multi and "\n" in out_multi

    # depth cutoff
    class C:
        x = 1

    assert kisrepr.object_repr(C(), _depth=2, max_depth=0) == "C(...)"

def test__repr_uses_custom_reprs_and_default_fallback_and_max_depth():
    class Custom:
        def __repr__(self):
            return "should-not-be-used"

    # attach a custom repr function
    def myrepr(obj, max_depth=7, depth=0):
        return "CUSTOM"

    kisrepr.custom_repr(Custom, myrepr)
    try:
        assert kisrepr._repr(Custom()) == "CUSTOM"
    finally:
        kisrepr.remove_custom_repr(Custom)

    # fallback to builtin repr for normal objects
    val = 12345
    assert kisrepr._repr(val) == repr(val)

    # max depth stops recursion
    nested = [ [ [1] ] ]
    assert kisrepr._repr(nested, max_depth=1, _depth=1) == "..."

def test_kis_repr_decorator_sets_repr_and_metadata():
    @kisrepr.kis_repr("x", "y", lines="single")
    class My:
        def __init__(self, x, y):
            self.x = x
            self.y = y

    inst = My(1, 2)
    r = inst.__repr__()  # use the generated repr
    assert "My(" in r and "x=1" in r and "y=2" in r

    # check that the generated function has expected attributes
    assert hasattr(My.__repr__, "__is_kis_repr__")
    assert My.__repr__.__name__ == "__repr__"


def test_custom_repr_management():
    class Tmp:
        pass

    def fn(obj, max_depth=7, depth=0):
        return "X"

    kisrepr.custom_repr(Tmp, fn)
    assert Tmp in kisrepr.custom_reprs
    assert kisrepr.custom_reprs[Tmp] is fn

    kisrepr.remove_custom_repr(Tmp)
    assert Tmp not in kisrepr.custom_reprs
