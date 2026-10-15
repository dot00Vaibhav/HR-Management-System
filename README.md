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

Open `http://localhost:8000` for the dashboard or `/docs` for the API reference. The app creates its indexes on startup. `GET /health` checks MongoDB readiness. Read `REVIEW.md` for starter findings and `DECISIONS.md` for implementation choices. Application and dashboard code are in `app/main.py`.
