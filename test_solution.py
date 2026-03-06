import pytest
from datetime import date, time, timedelta
from solution import TimeWindow, BusyInterval, Slot, suggest_slots

# C1: Suggested slots must lie within working hours (and candidate window if provided)
def test_slots_within_working_hours():
    day = date(2026, 1, 1)
    wh = TimeWindow(time(9, 0), time(10, 0))
    busy = []
    out = suggest_slots(day, wh, busy, timedelta(minutes=30), n=10)
    assert all(time(9, 0) <= s.start_time < time(10, 0) for s in out)
    assert all((timedelta(hours=s.start_time.hour, minutes=s.start_time.minute) + timedelta(minutes=30))
               <= timedelta(hours=10) for s in out)  # end <= 10:00


# C2: duration must be > 0 (invalid inputs raise ValueError)
def test_invalid_duration_raises():
    day = date(2026, 1, 1)
    wh = TimeWindow(time(9, 0), time(10, 0))
    with pytest.raises(ValueError):
        suggest_slots(day, wh, [], timedelta(minutes=0), n=1)


# C3: n must be >= 0 (invalid inputs raise ValueError)
def test_negative_n_raises():
    day = date(2026, 1, 1)
    wh = TimeWindow(time(9, 0), time(10, 0))
    with pytest.raises(ValueError):
        suggest_slots(day, wh, [], timedelta(minutes=15), n=-1)


# C4: busy intervals may be unsorted/overlapping; system must normalize them
def test_overlapping_and_unsorted_busy_intervals_normalized():
    day = date(2026, 1, 1)
    wh = TimeWindow(time(9, 0), time(12, 0))
    # overlaps and unsorted: [9:30-10:30] and [10:00-11:00] => merged to [9:30-11:00]
    busy = [
        BusyInterval(time(10, 0), time(11, 0)),
        BusyInterval(time(9, 30), time(10, 30)),
    ]
    out = suggest_slots(day, wh, busy, timedelta(minutes=30), n=10)
    # earliest valid slot should be 9:00 (ends 9:30) before merged busy starts at 9:30
    assert out[0].start_time == time(9, 0)


# C5: buffer must be respected (no slot can start within buffer after busy interval)
def test_buffer_respected_after_busy():
    day = date(2026, 1, 1)
    wh = TimeWindow(time(9, 0), time(11, 0))
    busy = [BusyInterval(time(9, 30), time(10, 0))]
    buf = timedelta(minutes=15)
    out = suggest_slots(day, wh, busy, timedelta(minutes=15), n=10, buffer=buf)
    # busy ends 10:00, buffer blocks until 10:15 => slot at 10:00 must not appear
    assert time(10, 0) not in [s.start_time for s in out]
    # slot at 10:15 is allowed (if it fits)
    assert time(10, 15) in [s.start_time for s in out]


# C6: candidate_window restricts suggestions (must lie within it)
def test_candidate_window_restricts():
    day = date(2026, 1, 1)
    wh = TimeWindow(time(9, 0), time(12, 0))
    cand = TimeWindow(time(10, 0), time(11, 0))
    out = suggest_slots(day, wh, [], timedelta(minutes=30), n=10, candidate_window=cand)
    assert all(time(10, 0) <= s.start_time < time(11, 0) for s in out)