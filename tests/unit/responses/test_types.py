from datetime import date, datetime, time
from decimal import Decimal

import pytest

from pykis.responses.types import (
    KisDynamicDict,
    KisAny,
    KisString,
    KisInt,
    KisFloat,
    KisDecimal,
    KisBool,
    KisDate,
    KisTime,
    KisDatetime,
    KisDict,
    KisTimeToDatetime,
)
from pykis.responses.dynamic import KisNoneValueError
from pykis.utils.timezone import TIMEZONE


def test_kis_dynamic_dict_from_and_getattr_and_repr():
    d = {"a": 1, "nested": {"b": 2}, "arr": [{"c": 3}, 4]}
    kd = KisDynamicDict.from_dict(d)

    assert kd.a == 1
    # nested returns KisDynamicDict
    nested = kd.nested
    assert isinstance(nested, KisDynamicDict)
    assert nested.b == 2
    # list mapping
    arr = kd.arr
    assert isinstance(arr[0], KisDynamicDict)
    assert arr[1] == 4
    # repr contains keys
    s = repr(kd)
    assert "a" in s and "nested" in s


def test_kis_any_transform_custom_and_default():
    anyt = KisAny(lambda v: "X" if v == "in" else {})
    assert anyt.transform("in") == "X"

    # default KisAny without arg returns KisDynamicDict when transforming
    any_default = KisAny()
    res = any_default.transform({"k": "v"})
    assert isinstance(res, KisDynamicDict)
    # default transform returns an empty KisDynamicDict instance (no __data__ set)
    # attempting to access attributes should raise AttributeError because __data__ is None
    with pytest.raises(AttributeError):
        _ = res.k


def test_basic_string_int_float_decimal_bool_transforms():
    s = KisString()
    assert s.transform(123) == "123"
    assert s.transform("abc") == "abc"

    i = KisInt()
    assert i.transform(5) == 5
    assert i.transform("42") == 42
    with pytest.raises(KisNoneValueError):
        i.transform("")

    f = KisFloat()
    assert f.transform(1.5) == 1.5
    assert f.transform("2.5") == 2.5
    with pytest.raises(KisNoneValueError):
        f.transform("")

    d = KisDecimal()
    assert d.transform("1.2300") == Decimal("1.23")
    with pytest.raises(KisNoneValueError):
        d.transform("")

    b = KisBool()
    assert b.transform(True) is True
    assert b.transform("Y") is True
    assert b.transform("true") is True
    assert b.transform(0) is False
    assert b.transform("n") is False


def test_date_time_datetime_and_dict_transforms():
    kd = KisDict()
    assert kd.transform({"x": 1}) == {"x": 1}
    with pytest.raises(KisNoneValueError):
        kd.transform("")

    kd_date = KisDate()
    dt = kd_date.transform("20250101")
    assert isinstance(dt, date)
    assert dt == datetime.strptime("20250101", "%Y%m%d").replace(tzinfo=TIMEZONE).date()

    kd_time = KisTime()
    t = kd_time.transform("235959")
    assert isinstance(t, time)
    assert t.hour == 23 and t.minute == 59 and t.second == 59

    kd_dt = KisDatetime()
    full = kd_dt.transform("20250101123045")
    assert isinstance(full, datetime)
    assert full.year == 2025 and full.hour == 12 and full.minute == 30 and full.second == 45


def test_time_to_datetime_transform():
    ktt = KisTimeToDatetime()
    res = ktt.transform("120000")
    assert isinstance(res, datetime)
    assert res.time().hour == 12 and res.time().minute == 0
