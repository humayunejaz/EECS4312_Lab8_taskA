import pytest
from datetime import date, time, timedelta
from solution import TimeWindow, BusyInterval, suggest_slots


# Covers C1, AC1
def test_slots_within_working_hours():
    day = date(2026, 1, 1)
    wh = TimeWindow(time(9, 0), time(10, 0))
    busy = []

    out = suggest_slots(day, wh, busy, timedelta(minutes=30), n=10)

    assert all(time(9, 0) <= s.start_time < time(10, 0) for s in out)
    assert out == sorted(out, key=lambda s: s.start_time)


# Covers C5, AC2
def test_overlapping_and_unsorted_busy_intervals_normalized():
    day = date(2026, 1, 1)
    wh = TimeWindow(time(9, 0), time(12, 0))
    busy = [
        BusyInterval(time(10, 0), time(11, 0)),
        BusyInterval(time(9, 30), time(10, 30)),
    ]

    out = suggest_slots(day, wh, busy, timedelta(minutes=30), n=10)

    assert out[0].start_time == time(9, 0)
    assert all(not (time(9, 30) <= s.start_time < time(11, 0)) for s in out)


# Covers C2, AC3
def test_buffer_respected_after_busy():
    day = date(2026, 1, 1)
    wh = TimeWindow(time(9, 0), time(11, 0))
    busy = [BusyInterval(time(9, 30), time(10, 0))]

    out = suggest_slots(
        day,
        wh,
        busy,
        timedelta(minutes=15),
        n=10,
        buffer=timedelta(minutes=15),
    )

    assert time(10, 0) not in [s.start_time for s in out]
    assert time(10, 15) in [s.start_time for s in out]


# Covers C4, AC4
def test_deterministic_ordering_same_input():
    day = date(2026, 1, 1)
    wh = TimeWindow(time(9, 0), time(11, 0))
    busy = [BusyInterval(time(9, 30), time(10, 0))]

    out1 = suggest_slots(day, wh, busy, timedelta(minutes=15), n=5)
    out2 = suggest_slots(day, wh, busy, timedelta(minutes=15), n=5)

    assert out1 == out2


# Covers C6, AC5
def test_no_slots_returns_empty():
    day = date(2026, 1, 1)
    wh = TimeWindow(time(9, 0), time(10, 0))
    busy = [BusyInterval(time(9, 0), time(10, 0))]

    out = suggest_slots(day, wh, busy, timedelta(minutes=15), n=5)

    assert out == []


# Covers C3, AC6
def test_returns_at_most_n_slots():
    day = date(2026, 1, 1)
    wh = TimeWindow(time(9, 0), time(12, 0))
    busy = []

    out = suggest_slots(day, wh, busy, timedelta(minutes=15), n=3)

    assert len(out) <= 3
    assert len(out) == 3


# Covers C5, AC1
def test_candidate_window_restricts():
    day = date(2026, 1, 1)
    wh = TimeWindow(time(9, 0), time(12, 0))
    cand = TimeWindow(time(10, 0), time(11, 0))

    out = suggest_slots(day, wh, [], timedelta(minutes=30), n=10, candidate_window=cand)

    assert all(time(10, 0) <= s.start_time < time(11, 0) for s in out)


# Covers C5, AC2
def test_small_gap_rejected():
    day = date(2026, 1, 1)
    wh = TimeWindow(time(9, 0), time(10, 0))
    busy = [
        BusyInterval(time(9, 0), time(9, 20)),
        BusyInterval(time(9, 30), time(10, 0)),
    ]

    out = suggest_slots(day, wh, busy, timedelta(minutes=15), n=10)

    assert out == []