"""MongoDB explain endpoint for the main analytical queries."""

from datetime import date

from fastapi import APIRouter, HTTPException, Query

from ..analytics.common import serialize_explain
from ..analytics.department_summary import dept_summary_pipeline
from ..analytics.department_trend import trend_pipeline
from ..analytics.employee_monthly import employee_month_pipeline
from ..analytics.late_leaderboard import leaderboard_pipeline
from ..attendance_rules import valid_date
from ..config import db
from .attendance import attendance_filter

router = APIRouter()


@router.get("/admin/explain/{endpoint}")
def explain(
    endpoint: str,
    emp_code: str | None = None,
    month: str | None = None,
    department: str | None = None,
    limit: int = Query(10, ge=1, le=50),
    date_from: str | None = None,
    date_to: str | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    from_date: str | None = Query(None, alias="from"),
    to_date: str | None = Query(None, alias="to"),
):
    if endpoint == "attendance_list":
        q = attendance_filter(emp_code, date_from, date_to, status)
        exp = db.command(
            "explain",
            {
                "find": "attendance_logs",
                "filter": q,
                "sort": {"date": -1, "emp_code": 1},
                "skip": (page - 1) * page_size,
                "limit": page_size,
            },
            verbosity="executionStats",
        )
        collection = "attendance_logs"
    elif endpoint == "employee_monthly":
        if not emp_code or not month:
            raise HTTPException(422, "emp_code and month are required")
        exp = db.command(
            "explain",
            {
                "aggregate": "attendance_logs",
                "pipeline": employee_month_pipeline(emp_code, month),
                "cursor": {},
            },
            verbosity="executionStats",
        )
        collection = "attendance_logs"
    elif endpoint == "department_summary":
        if not month:
            raise HTTPException(422, "month is required")
        exp = db.command(
            "explain",
            {
                "aggregate": "employees",
                "pipeline": dept_summary_pipeline(month, department),
                "cursor": {},
            },
            verbosity="executionStats",
        )
        collection = "employees"
    elif endpoint == "late_leaderboard":
        if not month:
            raise HTTPException(422, "month is required")
        exp = db.command(
            "explain",
            {
                "aggregate": "attendance_logs",
                "pipeline": leaderboard_pipeline(month, department, limit),
                "cursor": {},
            },
            verbosity="executionStats",
        )
        collection = "attendance_logs"
    elif endpoint == "department_trend":
        if not department or not from_date or not to_date:
            raise HTTPException(422, "department, from and to are required")
        valid_date(from_date)
        valid_date(to_date)
        first, last = date.fromisoformat(from_date), date.fromisoformat(to_date)
        if last < first or (last - first).days + 1 > 92:
            raise HTTPException(422, "invalid date range; maximum is 92 days")
        exp = db.command(
            "explain",
            {
                "aggregate": "employees",
                "pipeline": trend_pipeline(department, from_date, to_date),
                "cursor": {},
            },
            verbosity="executionStats",
        )
        collection = "employees"
    else:
        raise HTTPException(422, "unknown endpoint")
    return {
        "endpoint": endpoint,
        "collection": collection,
        "explain": serialize_explain(exp),
    }
