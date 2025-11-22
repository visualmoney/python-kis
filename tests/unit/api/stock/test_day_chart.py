from datetime import datetime, time, timedelta

from pykis.api.stock import day_chart


class _B:
    def __init__(self, t):
        self.time = t
        self.time_kst = t
        self.open = 1
        self.high = 2
        self.low = 1
        self.close = 1.5
        self.volume = 10
        self.amount = 100
        self.change = 0


def test_drop_after_time_range():
    """`drop_after` trims bars outside the given start/end range."""
    b1 = _B(datetime(2020, 1, 1, 9, 0))
    b2 = _B(datetime(2020, 1, 1, 10, 0))
    chart = type("C", (), {})()
    chart.bars = [b1, b2]

    res = day_chart.drop_after(chart, start=time(9, 30), end=time(10, 0))
    # result must be a list of bars within the requested time range (may be empty)
    assert isinstance(res.bars, list)
    for bar in res.bars:
        assert time(9, 30) <= bar.time.time() <= time(10, 0)


def test_domestic_day_chart_validations():
    """`domestic_day_chart` validates symbol and period parameters."""
    fake = type("K", (), {})()
    try:
        day_chart.domestic_day_chart(fake, "")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for empty symbol")

    try:
        day_chart.domestic_day_chart(fake, "SYM", period=0)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for invalid period")
