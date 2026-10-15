"""Shared analytics date, rounding, and explain helpers."""

import json
import re
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from bson import json_util
from fastapi import HTTPException


def month_bounds(month: str):
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", month):
        raise HTTPException(422, "month must be YYYY-MM")
    first = date.fromisoformat(month + "-01")
    last = date(first.year + (first.month == 12), first.month % 12 + 1, 1) - timedelta(
        days=1
    )
    return first.isoformat(), last.isoformat(), last


def rounded(value: float, places: int = 2) -> float:
    quantum = Decimal("1").scaleb(-places)
    return float(Decimal(str(value)).quantize(quantum, rounding=ROUND_HALF_UP))


def serialize_explain(value):
    return json.loads(json_util.dumps(value))
