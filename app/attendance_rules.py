"""Attendance date/time rules and public response serialization."""

import re
from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException

from .config import IST, PRESENCE, UTC


def valid_date(value: str) -> str:
    try:
        parsed = date.fromisoformat(value)
    except (ValueError, TypeError):
        raise HTTPException(422, "date must be YYYY-MM-DD")
    if parsed.isoformat() != value:
        raise HTTPException(422, "date must be YYYY-MM-DD")
    return value


def valid_instant(value: int | None) -> int | None:
    if value is None:
        return None
    if not 100_000_000_000 <= value <= 4_102_444_800_000:
        raise ValueError("timestamp must be epoch milliseconds")
    return value


def millis_to_dt(ms: int) -> datetime:
    return datetime(1970, 1, 1, tzinfo=UTC) + timedelta(milliseconds=ms - (ms % 1000))


def dt_to_millis(value: datetime | None) -> int | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return int(value.timestamp() * 1000)


def serial_dt(value):
    return dt_to_millis(value) if isinstance(value, datetime) else value


def public_record(doc: dict) -> dict:
    result = {k: v for k, v in doc.items() if k != "_id"}
    for k in ("punch_in", "punch_out"):
        result[k] = serial_dt(result.get(k))
    result["history"] = result.get("history") or []
    for item in result["history"]:
        item["at"] = serial_dt(item.get("at"))
        for change in item.get("changes", {}).values():
            change["from"] = serial_dt(change.get("from"))
            change["to"] = serial_dt(change.get("to"))
    result.setdefault("late_minutes", 0)
    result.setdefault("overtime_minutes", 0)
    result.setdefault("half_day", False)
    result.setdefault("work_hours", None)
    return result


def public_employee(doc: dict) -> dict:
    result = {k: v for k, v in doc.items() if k != "_id"}
    result["created_at"] = serial_dt(result.get("created_at"))
    return result


def hm(s: str) -> time:
    if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", s):
        raise ValueError("time must be HH:MM")
    h, m = map(int, s.split(":"))
    return time(h, m)


def trunc_seconds(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).replace(microsecond=0)


def shift_bounds(
    emp: dict, punch: datetime, attendance_date: str | None = None
) -> tuple[datetime, datetime]:
    local = punch.astimezone(IST)
    start_t, end_t = hm(emp["shift_start"]), hm(emp["shift_end"])
    d = date.fromisoformat(attendance_date) if attendance_date else local.date()
    overnight = end_t <= start_t
    if (
        attendance_date is None
        and overnight
        and local.timetz().replace(tzinfo=None) < end_t
    ):
        d -= timedelta(days=1)
    start_local = datetime.combine(d, start_t, IST)
    end_local = datetime.combine(
        d + (timedelta(days=1) if overnight else timedelta()), end_t, IST
    )
    return start_local.astimezone(UTC), end_local.astimezone(UTC)


def attendance_day(emp: dict, punch: datetime) -> str:
    local = punch.astimezone(IST)
    if hm(emp["shift_end"]) <= hm(emp["shift_start"]) and local.timetz().replace(
        tzinfo=None
    ) < hm(emp["shift_end"]):
        local -= timedelta(days=1)
    return local.date().isoformat()


def derived(
    emp: dict,
    status: str,
    punch_in: datetime | None,
    punch_out: datetime | None,
    day: str,
) -> dict:
    if status not in PRESENCE:
        return {
            "work_hours": None,
            "late_minutes": 0,
            "overtime_minutes": 0,
            "half_day": False,
        }
    if punch_in is None:
        raise HTTPException(422, "presence status requires punch_in")
    start, end = shift_bounds(emp, punch_in, day)
    delay = int((punch_in - start).total_seconds() // 60)
    late = delay if (punch_in - start).total_seconds() > 600 else 0
    if punch_out is None:
        return {
            "work_hours": None,
            "late_minutes": late,
            "overtime_minutes": 0,
            "half_day": False,
        }
    seconds = int((punch_out - punch_in).total_seconds())
    hours = float(
        (Decimal(seconds) / Decimal(3600)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    )
    over = int((punch_out - end).total_seconds() // 60)
    return {
        "work_hours": hours,
        "late_minutes": late,
        "overtime_minutes": over if over >= 30 else 0,
        "half_day": hours < 4.5,
    }
