"""Punch, correction, and attendance listing endpoints."""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pymongo import DESCENDING, ReturnDocument
from pymongo.errors import DuplicateKeyError

from ..attendance_rules import (
    attendance_day,
    derived,
    millis_to_dt,
    public_record,
    trunc_seconds,
    valid_date,
)
from ..config import PRESENCE, STATUSES, UTC, db
from ..schemas import PunchInIn, PunchOutIn, RegularizeIn

router = APIRouter()


@router.post("/attendance/punch-in", status_code=201)
def punch_in(body: PunchInIn):
    emp = db.employees.find_one({"emp_code": body.emp_code})
    if not emp:
        raise HTTPException(404, "employee not found")
    ts = (
        trunc_seconds(millis_to_dt(body.punched_at))
        if body.punched_at is not None
        else datetime.now(UTC).replace(microsecond=0)
    )
    day = attendance_day(emp, ts)
    doc = {
        "emp_code": body.emp_code,
        "date": day,
        "status": body.status,
        "punch_in": ts,
        "punch_out": None,
        "work_hours": None,
        "late_minutes": derived(emp, body.status, ts, None, day)["late_minutes"],
        "overtime_minutes": 0,
        "half_day": False,
        "history": [],
    }
    try:
        db.attendance_logs.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(409, "already punched in for this date")
    return public_record(doc)


def attendance_filter(emp_code=None, date_from=None, date_to=None, status=None):
    q = {}
    if emp_code is not None:
        q["emp_code"] = emp_code
    if date_from or date_to:
        q["date"] = {}
        if date_from:
            q["date"]["$gte"] = valid_date(date_from)
        if date_to:
            q["date"]["$lte"] = valid_date(date_to)
        if date_from and date_to and date_from > date_to:
            raise HTTPException(422, "date_from must not exceed date_to")
    if status is not None:
        if status not in STATUSES:
            raise HTTPException(422, "invalid status")
        q["status"] = status
    return q


@router.get("/attendance")
def list_attendance(
    emp_code: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    q = attendance_filter(emp_code, date_from, date_to, status)
    total = db.attendance_logs.count_documents(q)
    docs = (
        db.attendance_logs.find(q, {"_id": 0})
        .sort([("date", DESCENDING), ("emp_code", ASCENDING)])
        .skip((page - 1) * page_size)
        .limit(page_size)
    )
    return {
        "items": [public_record(d) for d in docs],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/attendance/punch-out")
def punch_out(body: PunchOutIn):
    emp = db.employees.find_one({"emp_code": body.emp_code})
    if not emp:
        raise HTTPException(404, "employee not found")
    ts = (
        trunc_seconds(millis_to_dt(body.punched_at))
        if body.punched_at is not None
        else datetime.now(UTC).replace(microsecond=0)
    )
    doc = db.attendance_logs.find_one(
        {
            "emp_code": body.emp_code,
            "punch_in": {"$lte": ts},
            "status": {"$in": PRESENCE},
        },
        sort=[("punch_in", DESCENDING)],
    )
    if not doc:
        raise HTTPException(404, "no punch-in found")
    pi = trunc_seconds(doc["punch_in"])
    seconds = (ts - pi).total_seconds()
    if seconds <= 0 or seconds > 86400:
        raise HTTPException(422, "punch_out must be after punch_in and within 24 hours")
    values = derived(emp, doc["status"], pi, ts, doc["date"])
    updated = db.attendance_logs.find_one_and_update(
        {"_id": doc["_id"], "punch_out": None},
        {"$set": {"punch_in": pi, "punch_out": ts, **values}},
        return_document=ReturnDocument.AFTER,
    )
    if updated is None:
        raise HTTPException(409, "record is already punched out")
    return public_record(updated)


@router.patch("/attendance/{emp_code}/{date}")
def regularize(emp_code: str, date: str, body: RegularizeIn):
    valid_date(date)
    emp = db.employees.find_one({"emp_code": emp_code})
    if not emp:
        raise HTTPException(404, "employee not found")
    old = db.attendance_logs.find_one({"emp_code": emp_code, "date": date})
    if not old:
        raise HTTPException(404, "attendance record not found")
    status = body.status if body.status is not None else old["status"]
    if status in ("ABSENT", "LEAVE") and (
        body.punch_in is not None or body.punch_out is not None
    ):
        raise HTTPException(422, "ABSENT and LEAVE cannot have punch times")
    pin = (
        millis_to_dt(body.punch_in)
        if body.punch_in is not None
        else old.get("punch_in")
    )
    pout = (
        millis_to_dt(body.punch_out)
        if body.punch_out is not None
        else old.get("punch_out")
    )
    if status in ("ABSENT", "LEAVE"):
        pin = pout = None
    if status in PRESENCE and pin is None:
        raise HTTPException(422, "presence status requires punch_in")
    if pin is not None and attendance_day(emp, pin) != date:
        raise HTTPException(422, "punch_in must belong to attendance date")
    if pout is not None:
        if pin is None or pout <= pin or (pout - pin).total_seconds() > 86400:
            raise HTTPException(422, "invalid punch_out")
        pout = trunc_seconds(pout)
    if pin is not None:
        pin = trunc_seconds(pin)
    computed = derived(emp, status, pin, pout, date)
    final = {"status": status, "punch_in": pin, "punch_out": pout, **computed}
    changed = {}
    for key, value in final.items():
        prior = old.get(key)
        if isinstance(prior, datetime):
            prior = trunc_seconds(prior)
        if prior != value:
            changed[key] = {"from": prior, "to": value}
    if not changed:
        raise HTTPException(422, "request does not change the record")
    entry = {
        "at": datetime.now(UTC).replace(microsecond=0),
        "by": body.regularized_by,
        "reason": body.reason,
        "changes": changed,
    }
    history_guard = (
        {"history": old["history"]}
        if "history" in old
        else {"history": {"$exists": False}}
    )
    updated = db.attendance_logs.find_one_and_update(
        {"_id": old["_id"], **history_guard},
        {"$set": final, "$push": {"history": entry}},
        return_document=ReturnDocument.AFTER,
    )
    if updated is None:
        raise HTTPException(409, "record changed concurrently")
    return public_record(updated)
