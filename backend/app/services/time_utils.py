from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_TIMEZONE = "Asia/Kolkata"


def get_zone(name: str | None) -> ZoneInfo:
    try:
        return ZoneInfo(name or DEFAULT_TIMEZONE)
    except (ZoneInfoNotFoundError, ValueError):
        return ZoneInfo("UTC")


def ensure_utc(
    value: datetime,
    tz_name: str | None = DEFAULT_TIMEZONE,
) -> datetime:
    """Normalize a datetime to UTC.

    Naive values are interpreted in the station's local timezone so API
    clients can send either local wall time or an aware timestamp.
    """

    if value.tzinfo is None:
        value = value.replace(tzinfo=get_zone(tz_name))

    return value.astimezone(timezone.utc)


def as_utc(value: datetime) -> datetime:
    """Treat a stored timestamp as UTC, even when the driver returns naive."""

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def local_time(value: datetime, tz_name: str | None) -> datetime:
    return value.astimezone(get_zone(tz_name))


def local_iso(value: datetime, tz_name: str | None) -> str:
    return local_time(value, tz_name).isoformat()


def align_up(value: datetime, minutes: int, tz_name: str | None) -> datetime:
    """Round a UTC instant up to the next local slot boundary."""

    zone = get_zone(tz_name)
    local = value.astimezone(zone)

    remainder = local.minute % minutes
    add_minutes = 0 if remainder == 0 and local.second == 0 and local.microsecond == 0 else minutes - remainder

    local = (
        local.replace(second=0, microsecond=0)
        + timedelta(minutes=add_minutes)
    )

    return local.astimezone(timezone.utc)


def is_aligned(value: datetime, minutes: int, tz_name: str | None) -> bool:
    local = value.astimezone(get_zone(tz_name))
    return local.minute % minutes == 0 and local.second == 0
