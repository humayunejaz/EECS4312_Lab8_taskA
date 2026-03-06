## Student Name: Humayun Ejaz
## Student ID: 219476837

from __future__ import annotations

"""
Task A: Appointment Timeslot Recommender (Stub)

In this lab, you will design and implement an Appointment Slot Recommender using an LLM assistant
as your primary programming collaborator.

You are asked to implement a Python module that recommends available meeting slots within a
defined working window.

The system must:
  • Accept working hours (start and end time).
  • Accept a list of existing busy intervals.
  • Accept a required meeting duration.
  • Accept an optional buffer time between meetings.
  • Optionally restrict suggestions to a candidate time window.
  • Return chronologically ordered appointment slots that satisfy all constraints.

The system must ensure that:
  • Suggested slots fall within working hours.
  • Suggested slots do not overlap busy intervals.
  • Buffer time is respected when evaluating availability.
  • Output ordering is deterministic under identical inputs.

The module must preserve the following invariants:
  • Returned slots must be at least as long as the required duration.
  • No returned slot may violate buffer constraints.
  • The returned list must reflect the current system state.

The system must correctly handle non-trivial scenarios such as:
  • Adjacent busy intervals.
  • Very small gaps between meetings.
  • Buffers eliminating otherwise valid availability.
  • Overlapping or unsorted busy intervals.
  • A meeting duration longer than any available gap.
  • No availability within the working window.

Output:
  The output consists of the next N valid appointment suggestions in chronological order.
  Behavior must be deterministic under ties (if any).

See the lab handout for full requirements.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, time
from typing import List, Optional, Tuple


# ---------------- Data Models ----------------

@dataclass(frozen=True)
class TimeWindow:
    """
    A daily time window.
    Assumption (unless stated otherwise in handout): non-wrapping window where start < end.
    """
    start: time
    end: time


@dataclass(frozen=True)
class BusyInterval:
    """
    A busy interval on the given day.
    Invariant: start < end
    """
    start: time
    end: time


@dataclass(frozen=True)
class Slot:
    """
    A recommended appointment slot.

    start_time is a time-of-day within the working window.
    Deterministic ordering: sort by start_time ascending.
    """
    start_time: time


class InfeasibleSchedule(Exception):
    """Raised when no valid slots can be produced (if required by handout)."""
    pass


# ---------------- Core Function ----------------

def suggest_slots(
    day: date,
    working_hours: TimeWindow,
    busy_intervals: List[BusyInterval],
    duration: timedelta,
    n: int,
    buffer: timedelta = timedelta(0),
    candidate_window: Optional[TimeWindow] = None
) -> List[Slot]:
    """
    Suggest up to the next n valid appointment slots (start times) for the given day.

    Args:
        day: the calendar day for which to suggest slots.
        working_hours: the allowed working window for meetings (start < end).
        busy_intervals: list of busy time intervals (may be overlapping / unsorted).
        duration: required meeting length (must be > 0).
        n: maximum number of slot suggestions to return (n >= 0).
        buffer: optional buffer time required between meetings (buffer >= 0).
        candidate_window: optional extra restriction on suggestions (must lie within this window too).

    Returns:
        A list of Slot objects, sorted by start_time ascending, deterministic under identical inputs.
        If no suitable time slots are available, return an empty list.

    Notes:
        - Suggested slots must fall within working_hours (and candidate_window if provided).
        - Suggested slots must not overlap busy_intervals, considering buffer time.
        - Internal search is minute-granularity (1-minute increments) unless handout states otherwise.
    """
    # ---------- input validation ----------
    if duration <= timedelta(0):
        raise ValueError("duration must be > 0")
    if n < 0:
        raise ValueError("n must be >= 0")
    if buffer < timedelta(0):
        raise ValueError("buffer must be >= 0")
    if working_hours.start >= working_hours.end:
        raise ValueError("working_hours must satisfy start < end")
    if candidate_window is not None and candidate_window.start >= candidate_window.end:
        raise ValueError("candidate_window must satisfy start < end")

    if n == 0:
        return []

    # ---------- helpers ----------
    def to_dt(t: time) -> datetime:
        return datetime.combine(day, t)

    def clamp_interval(
        s: datetime,
        e: datetime,
        lo: datetime,
        hi: datetime
    ) -> Optional[Tuple[datetime, datetime]]:
        s2 = max(s, lo)
        e2 = min(e, hi)
        if s2 < e2:
            return (s2, e2)
        return None

    def merge_intervals(intervals: List[Tuple[datetime, datetime]]) -> List[Tuple[datetime, datetime]]:
        if not intervals:
            return []
        intervals.sort(key=lambda x: x[0])
        merged: List[Tuple[datetime, datetime]] = [intervals[0]]
        for s, e in intervals[1:]:
            ps, pe = merged[-1]
            # merge if overlapping or touching
            if s <= pe:
                merged[-1] = (ps, max(pe, e))
            else:
                merged.append((s, e))
        return merged

    # ---------- compute allowed window ----------
    work_lo = to_dt(working_hours.start)
    work_hi = to_dt(working_hours.end)

    allowed_lo, allowed_hi = work_lo, work_hi
    if candidate_window is not None:
        cand_lo = to_dt(candidate_window.start)
        cand_hi = to_dt(candidate_window.end)
        allowed_lo = max(allowed_lo, cand_lo)
        allowed_hi = min(allowed_hi, cand_hi)

    if allowed_lo >= allowed_hi:
        return []

    # ---------- normalize + buffer busy intervals ----------
    blocked: List[Tuple[datetime, datetime]] = []

    for bi in busy_intervals:
        # Guard even though invariant says start < end
        if bi.start >= bi.end:
            continue

        # Buffer rule: block before + after busy interval (clamped to allowed window)
        s = to_dt(bi.start) - buffer
        e = to_dt(bi.end) + buffer

        clamped = clamp_interval(s, e, allowed_lo, allowed_hi)
        if clamped is not None:
            blocked.append(clamped)

    blocked = merge_intervals(blocked)

    # ---------- scan for slots ----------
    results: List[Slot] = []
    step = timedelta(minutes=1)
    cursor = allowed_lo

    # If there are no blocked intervals, fill from allowed_lo
    if not blocked:
        while cursor + duration <= allowed_hi and len(results) < n:
            results.append(Slot(start_time=cursor.time()))
            cursor += step
        return results

    for b_start, b_end in blocked:
        # free region is [cursor, b_start)
        while cursor + duration <= b_start and len(results) < n:
            results.append(Slot(start_time=cursor.time()))
            cursor += step

        if len(results) >= n:
            return results

        # jump cursor past blocked region
        if cursor < b_end:
            cursor = b_end

        if cursor >= allowed_hi:
            return results

    # after last blocked region, free region is [cursor, allowed_hi)
    while cursor + duration <= allowed_hi and len(results) < n:
        results.append(Slot(start_time=cursor.time()))
        cursor += step

    return results