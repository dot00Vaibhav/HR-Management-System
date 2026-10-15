"""Route assembly for employees, attendance, analytics, and explain plans."""

from fastapi import APIRouter

from .employees import router as employees_router
from .attendance import router as attendance_router
from .analytics import router as analytics_router
from .admin import router as admin_router

api_router = APIRouter()
api_router.include_router(employees_router)
api_router.include_router(attendance_router)
api_router.include_router(analytics_router)
api_router.include_router(admin_router)
