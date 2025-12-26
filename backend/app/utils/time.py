"""
Time Utilities
backend/app/utils/time.py

Centralized time functions to avoid deprecated datetime.utcnow()
"""
from datetime import datetime, timezone, timedelta
from typing import Optional


def utcnow() -> datetime:
    """
    Return current UTC datetime with timezone info.
    Replaces deprecated datetime.utcnow() (Python 3.12+)
    """
    return datetime.now(timezone.utc)


def utc_date_today() -> datetime:
    """Return today's date at midnight UTC."""
    now = utcnow()
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def days_ago(days: int) -> datetime:
    """Return datetime N days ago from now."""
    return utcnow() - timedelta(days=days)


def days_between(start: datetime, end: Optional[datetime] = None) -> int:
    """Calculate days between two datetimes."""
    if end is None:
        end = utcnow()
    # Handle naive datetimes by assuming UTC
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    return (end - start).days


def iso_now() -> str:
    """Return current UTC time as ISO string."""
    return utcnow().isoformat()
