"""
MCP 공통 유틸리티 - 검증 함수
"""
from typing import Optional
from uuid import UUID


def validate_uuid(value: str) -> Optional[UUID]:
    """Validate and convert string to UUID, return None if invalid"""
    try:
        return UUID(value)
    except (ValueError, TypeError):
        return None


def safe_format_number(value, default: str = "N/A") -> str:
    """Safely format number with commas, return default if None or invalid"""
    if value is None:
        return default
    if isinstance(value, str):
        return default
    try:
        return f"{value:,}"
    except (ValueError, TypeError):
        return default
