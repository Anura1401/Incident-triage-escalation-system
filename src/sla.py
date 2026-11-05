"""
SLA Calculation Module for Simulated Teleoperation Incident Management.
Mirrors Airtable formula logic exactly.
ALL DATA IS SYNTHETIC. NO REAL CUSTOMER OR ROBOT DATA.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from src.rules import get_priority_sla


def _parse_dt(dt_val: Optional[Union[str, datetime]]) -> Optional[datetime]:
    """Parse an ISO date string or return timezone-aware UTC datetime."""
    if dt_val is None or dt_val == "":
        return None
    if isinstance(dt_val, datetime):
        if dt_val.tzinfo is None:
            return dt_val.replace(tzinfo=timezone.utc)
        return dt_val.astimezone(timezone.utc)

    str_val = str(dt_val).strip()
    if not str_val:
        return None

    # Handle ISO string with trailing Z or offset
    if str_val.endswith("Z"):
        str_val = str_val[:-1] + "+00:00"

    try:
        dt = datetime.fromisoformat(str_val)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(str_val, fmt)
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        raise ValueError(f"Unable to parse datetime: {dt_val}")


def response_due(created_at: Union[str, datetime], priority: str) -> datetime:
    """Calculate the first response deadline for a ticket."""
    created = _parse_dt(created_at)
    if created is None:
        raise ValueError("created_at cannot be None")
    resp_minutes, _ = get_priority_sla(priority)
    return created + timedelta(minutes=resp_minutes)


def resolution_due(created_at: Union[str, datetime], priority: str) -> datetime:
    """Calculate the target resolution deadline for a ticket."""
    created = _parse_dt(created_at)
    if created is None:
        raise ValueError("created_at cannot be None")
    _, res_hours = get_priority_sla(priority)
    return created + timedelta(hours=res_hours)


def response_breached(
    created_at: Union[str, datetime],
    priority: str,
    first_response_at: Optional[Union[str, datetime]],
    now: Union[str, datetime]
) -> bool:
    """
    Check if response SLA was breached.
    - If first response is missing: breached if now > response_due.
    - If first response exists: breached if first_response_at > response_due.
    """
    due = response_due(created_at, priority)
    curr_now = _parse_dt(now)
    resp = _parse_dt(first_response_at)

    if resp is None:
        return curr_now > due
    return resp > due


def resolution_breached(
    created_at: Union[str, datetime],
    priority: str,
    status: str,
    resolved_at: Optional[Union[str, datetime]],
    now: Union[str, datetime]
) -> bool:
    """
    Check if resolution SLA was breached.
    - If resolved: breached if resolved_at > resolution_due.
    - If unresolved: breached if now > resolution_due.
    """
    due = resolution_due(created_at, priority)
    curr_now = _parse_dt(now)
    res = _parse_dt(resolved_at)

    if (status or "").strip().lower() == "resolved":
        if res is None:
            return curr_now > due
        return res > due
    return curr_now > due


def time_to_resolve_hours(
    created_at: Union[str, datetime],
    resolved_at: Optional[Union[str, datetime]]
) -> Optional[float]:
    """Calculate time to resolve in hours rounded to 2 decimal places."""
    created = _parse_dt(created_at)
    res = _parse_dt(resolved_at)
    if created is None or res is None:
        return None
    diff_sec = (res - created).total_seconds()
    return round(diff_sec / 3600.0, 2)


def age_hours(
    created_at: Union[str, datetime],
    status: str,
    now: Union[str, datetime]
) -> Optional[float]:
    """Calculate ticket age in hours for open/in-progress tickets."""
    if (status or "").strip().lower() == "resolved":
        return None
    created = _parse_dt(created_at)
    curr_now = _parse_dt(now)
    if created is None or curr_now is None:
        return None
    diff_sec = (curr_now - created).total_seconds()
    return round(diff_sec / 3600.0, 1)
