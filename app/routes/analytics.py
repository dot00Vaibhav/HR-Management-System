"""Employee and department analytics endpoints."""

from datetime import date

from fastapi import APIRouter, HTTPException, Query

from ..analytics.common import month_bounds, rounded
from ..analytics.department_summary import dept_summary_pipeline
from ..analytics.department_trend import trend_pipeline
from ..analytics.employee_monthly import (
    employee_month_pipeline,
    employee_working_days_pipeline,
)
from ..analytics.late_leaderboard import leaderboard_pipeline
from ..attendance_rules import valid_date
from ..config import db

router = APIRouter()


@router.get("/analytics/employees/{emp_code}/monthly")
def employee_monthly(emp_code: str, month: str):
    start, end, _ = month_bounds(month)
    emp = db.employees.find_one({"emp_code": emp_code}, {"_id": 1, "joined_on": 1})
    if not emp:
        raise HTTPException(404, "employee not found")
    result = list(
        db.attendance_logs.aggregate(employee_month_pipeline(emp_code, month))
    )
    row = result[0] if result else {}
    work_days = list(
        db.employees.aggregate(employee_working_days_pipeline(emp_code, month))
    )
    wd = work_days[0]["working_days"] if work_days else 0
    present = rounded(float(row.get("present_days", 0)))
    return {
        "emp_code": emp_code,
        "month": month,
        "working_days": wd,
        "present_days": present,
        "leave_days": row.get("leave_days", 0),
        "late_count": row.get("late_count", 0),
        "total_late_minutes": row.get("total_late_minutes", 0),
        "total_overtime_minutes": row.get("total_overtime_minutes", 0),
        "attendance_pct": rounded(present / wd * 100) if wd else None,
    }


@router.get("/analytics/departments/summary")
def department_summary(month: str, department: str | None = None):
    month_bounds(month)
    rows = list(
        db.employees.aggregate(
            dept_summary_pipeline(month, department), allowDiskUse=True
        )
    )
    for r in rows:
        r["present_days"] = rounded(float(r["present_days"]))
        if r["avg_work_hours"] is not None:
            r["avg_work_hours"] = rounded(float(r["avg_work_hours"]))
    return {"month": month, "items": rows}


@router.get("/analytics/leaderboard/late")
def late_leaderboard(
    month: str, limit: int = Query(10, ge=1, le=50), department: str | None = None
):
    month_bounds(month)
    rows = list(
        db.attendance_logs.aggregate(
            leaderboard_pipeline(month, department, limit), allowDiskUse=True
        )
    )
    return {"month": month, "items": rows}


@router.get("/analytics/departments/{department}/trend")
def department_trend(
    department: str,
    from_date: str = Query(..., alias="from"),
    to_date: str = Query(..., alias="to"),
):
    valid_date(from_date)
    valid_date(to_date)
    first, last = date.fromisoformat(from_date), date.fromisoformat(to_date)
    if last < first or (last - first).days + 1 > 92:
        raise HTTPException(422, "invalid date range; maximum is 92 days")
    if not db.employees.find_one({"department": department}, {"_id": 1}):
        raise HTTPException(404, "department not found")
    rows = list(
        db.attendance_logs.aggregate(
            trend_pipeline(department, from_date, to_date), allowDiskUse=True
        )
    )
    # Decimal half-up is applied to the reported rates to avoid binary/banker's rounding.
    for r in rows:
        for key in ("attendance_rate", "moving_avg_7d"):
            if r[key] is not None:
                r[key] = rounded(float(r[key]), 4)
    return {"department": department, "items": rows}
