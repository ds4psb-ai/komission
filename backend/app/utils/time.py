"""
Time Utilities
backend/app/utils/time.py

Centralized time functions to avoid deprecated datetime.utcnow()
"""
from datetime import datetime, timezone, timedelta
from typing import Optional
import uuid


def utcnow() -> datetime:
    """
    Return current UTC datetime as naive (no timezone info).
    
    PostgreSQL uses TIMESTAMP WITHOUT TIME ZONE, so we need naive datetimes.
    Uses datetime.now(timezone.utc).replace(tzinfo=None) to get accurate UTC
    time while maintaining DB compatibility.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


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
    """Return current UTC time as ISO string (no Z suffix)."""
    return utcnow().isoformat()


def iso_now_z() -> str:
    """Return current UTC time as ISO string with Z suffix."""
    return utcnow().isoformat() + "Z"


# ====================
# ID GENERATION UTILITIES
# ====================

def generate_uuid() -> str:
    """Generate random UUID string."""
    return str(uuid.uuid4())


def generate_short_id(prefix: str = "") -> str:
    """Generate short 12-char hex ID with optional prefix."""
    short = uuid.uuid4().hex[:12]
    return f"{prefix}_{short}" if prefix else short


def generate_event_id() -> str:
    """Generate event ID with evt_ prefix."""
    return f"evt_{uuid.uuid4().hex[:12]}"


def generate_intervention_id() -> str:
    """Generate intervention ID with iv_ prefix."""
    return f"iv_{uuid.uuid4().hex[:12]}"


def generate_session_id() -> str:
    """Generate session ID (full UUID)."""
    return str(uuid.uuid4())


def generate_pack_id() -> str:
    """Generate pack ID (full UUID)."""
    return str(uuid.uuid4())
