"""FastAPI application setup and browser-facing routes."""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response

from .config import ensure_indexes
from .dashboard import FAVICON_SVG, INDEX_HTML, NOT_FOUND_HTML
from .routes import api_router

app = FastAPI(title="Employee Attendance & Analytics API", version="2.0.0")
app.include_router(api_router)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home():
    return HTMLResponse(INDEX_HTML)


@app.get("/favicon.svg", include_in_schema=False)
def favicon():
    return Response(content=FAVICON_SVG, media_type="image/svg+xml")


@app.exception_handler(404)
async def custom_not_found(request: Request, exc):
    if "text/html" in request.headers.get("accept", ""):
        return HTMLResponse(NOT_FOUND_HTML, status_code=404)
    return JSONResponse(
        {"detail": getattr(exc, "detail", "Not found")}, status_code=404
    )


@app.on_event("startup")
def startup_indexes():
    ensure_indexes()
