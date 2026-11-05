"""
Unit Tests for SLA Calculation Module.
Validates exact deadline offsets, breach conditions, resolution times, and age metrics.
"""

from datetime import datetime, timezone
import pytest
from src.sla import (
    response_due,
    resolution_due,
    response_breached,
    resolution_breached,
    time_to_resolve_hours,
    age_hours,
)

# Deterministic evaluation reference timestamp
FIXED_NOW = datetime(2026, 11, 5, 18, 0, 0, tzinfo=timezone.utc)
FIXED_CREATED = datetime(2026, 11, 5, 10, 0, 0, tzinfo=timezone.utc)


def test_p1_sla_deadlines():
    # P1: 15 min response, 4 h resolution
    r_due = response_due(FIXED_CREATED, "P1")
    res_due = resolution_due(FIXED_CREATED, "P1")
    assert r_due == datetime(2026, 11, 5, 10, 15, 0, tzinfo=timezone.utc)
    assert res_due == datetime(2026, 11, 5, 14, 0, 0, tzinfo=timezone.utc)


def test_p2_sla_deadlines():
    # P2: 2 h response, 12 h resolution
    r_due = response_due(FIXED_CREATED, "P2")
    res_due = resolution_due(FIXED_CREATED, "P2")
    assert r_due == datetime(2026, 11, 5, 12, 0, 0, tzinfo=timezone.utc)
    assert res_due == datetime(2026, 11, 5, 22, 0, 0, tzinfo=timezone.utc)


def test_p3_sla_deadlines():
    # P3: 8 h response, 48 h resolution
    r_due = response_due(FIXED_CREATED, "P3")
    res_due = resolution_due(FIXED_CREATED, "P3")
    assert r_due == datetime(2026, 11, 5, 18, 0, 0, tzinfo=timezone.utc)
    assert res_due == datetime(2026, 11, 7, 10, 0, 0, tzinfo=timezone.utc)


def test_p4_sla_deadlines():
    # P4: 24 h response, 120 h (5 days) resolution
    r_due = response_due(FIXED_CREATED, "P4")
    res_due = resolution_due(FIXED_CREATED, "P4")
    assert r_due == datetime(2026, 11, 6, 10, 0, 0, tzinfo=timezone.utc)
    assert res_due == datetime(2026, 11, 10, 10, 0, 0, tzinfo=timezone.utc)


def test_response_breach_missing_response():
    # Created at 10:00. P1 due at 10:15.
    # At 10:10 (before due): not breached
    now_early = datetime(2026, 11, 5, 10, 10, 0, tzinfo=timezone.utc)
    assert response_breached(FIXED_CREATED, "P1", None, now_early) is False

    # At 10:20 (past due): breached
    now_late = datetime(2026, 11, 5, 10, 20, 0, tzinfo=timezone.utc)
    assert response_breached(FIXED_CREATED, "P1", None, now_late) is True


def test_response_breach_with_response_time():
    # Created at 10:00. P1 due at 10:15.
    # Responded at 10:12: not breached even if evaluated at 18:00
    resp_on_time = datetime(2026, 11, 5, 10, 12, 0, tzinfo=timezone.utc)
    assert response_breached(FIXED_CREATED, "P1", resp_on_time, FIXED_NOW) is False

    # Responded at 10:25: breached
    resp_late = datetime(2026, 11, 5, 10, 25, 0, tzinfo=timezone.utc)
    assert response_breached(FIXED_CREATED, "P1", resp_late, FIXED_NOW) is True


def test_resolution_breach_resolved_ticket():
    # Created at 10:00. P1 due at 14:00.
    # Resolved at 13:30 -> Not breached
    res_on_time = datetime(2026, 11, 5, 13, 30, 0, tzinfo=timezone.utc)
    assert resolution_breached(FIXED_CREATED, "P1", "Resolved", res_on_time, FIXED_NOW) is False

    # Resolved at 14:45 -> Breached
    res_late = datetime(2026, 11, 5, 14, 45, 0, tzinfo=timezone.utc)
    assert resolution_breached(FIXED_CREATED, "P1", "Resolved", res_late, FIXED_NOW) is True


def test_resolution_breach_open_ticket():
    # Created at 10:00. P1 resolution due at 14:00.
    # At 12:00 -> not breached yet
    now_before_due = datetime(2026, 11, 5, 12, 0, 0, tzinfo=timezone.utc)
    assert resolution_breached(FIXED_CREATED, "P1", "Open", None, now_before_due) is False

    # At 15:00 -> breached
    now_after_due = datetime(2026, 11, 5, 15, 0, 0, tzinfo=timezone.utc)
    assert resolution_breached(FIXED_CREATED, "P1", "Open", None, now_after_due) is True


def test_time_to_resolve_hours():
    created = datetime(2026, 11, 5, 10, 0, 0, tzinfo=timezone.utc)
    resolved = datetime(2026, 11, 5, 14, 30, 0, tzinfo=timezone.utc)
    ttr = time_to_resolve_hours(created, resolved)
    assert ttr == 4.50

    # Unresolved ticket returns None
    assert time_to_resolve_hours(created, None) is None


def test_age_hours():
    created = datetime(2026, 11, 5, 10, 0, 0, tzinfo=timezone.utc)
    now = datetime(2026, 11, 5, 16, 30, 0, tzinfo=timezone.utc)
    # Open ticket: 6.5 hours
    assert age_hours(created, "Open", now) == 6.5
    # Resolved ticket: None
    assert age_hours(created, "Resolved", now) is None

