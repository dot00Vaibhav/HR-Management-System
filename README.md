# Employee Attendance & Analytics API

FastAPI and MongoDB service for employee records, attendance punches, manual corrections, and monthly/department analytics. Includes a responsive management dashboard at `/`. Requires Python 3.11+ and MongoDB 6.0+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:MONGO_URI = "mongodb://localhost:27017"
$env:MONGO_DB = "attendance_db"
uvicorn app.main:app --port 8000
```

Open `http://localhost:8000` for the dashboard or `/docs` for the API reference. The app creates its indexes on startup. `GET /health` checks MongoDB readiness. Read `REVIEW.md` for starter findings and `DECISIONS.md` for implementation choices. The app is assembled in `app/main.py`; see the code layout below to find each area.


## Code layout

- `app/main.py` creates the FastAPI app and serves the dashboard and favicon.
- `app/config.py` configures MongoDB, shared constants, and indexes.
- `.python-version` pins the verified Python runtime used by Render.
- `app/schemas.py` validates request payloads.
- `app/attendance_rules.py` contains IST/date-time rules and response serialization.
- `app/analytics/` contains shared analytics helpers and one module per report pipeline.
- `app/routes/` groups HTTP endpoints by employees, attendance, analytics, and explain plans.
- `app/dashboard.py` contains the responsive HTML, CSS, and browser JavaScript.
