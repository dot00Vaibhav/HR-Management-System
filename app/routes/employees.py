"""Employee directory endpoints and the MongoDB readiness endpoint."""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pymongo import ASCENDING
from pymongo.errors import DuplicateKeyError

from ..attendance_rules import public_employee
from ..config import UTC, client, db
from ..schemas import EmployeeIn

router = APIRouter()


@router.get("/health")
def health():
    try:
        client.admin.command("ping")
    except Exception:
        raise HTTPException(503, "MongoDB unavailable")
    return {"status": "ok"}


@router.post("/employees", status_code=201)
def create_employee(body: EmployeeIn):
    doc = body.model_dump()
    doc["created_at"] = datetime.now(UTC).replace(microsecond=0)
    try:
        db.employees.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(409, "emp_code already exists")
    return public_employee(doc)


@router.get("/employees")
def list_employees(
    department: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    q = {"department": department} if department is not None else {}
    total = db.employees.count_documents(q)
    items = [
        public_employee(d)
        for d in db.employees.find(q, {"_id": 0})
        .sort("emp_code", ASCENDING)
        .skip((page - 1) * page_size)
        .limit(page_size)
    ]
    return {"items": items, "total": total, "page": page, "page_size": page_size}
