# Employee Attendance & Analytics API

FastAPI and MongoDB service for employee records, attendance punches, manual corrections, monthly/department analytics, and a browser dashboard at /.

## Requirements

- Python 3.11 or newer
- MongoDB 6.0 or newer, running locally or reachable through MongoDB Atlas

## Run locally (Windows PowerShell)

Open a terminal at the repository root. Start MongoDB first. If Docker is installed, you can run MongoDB in a container:

~~~powershell
docker run --name attendance-mongo --publish 27017:27017 --detach mongo:7
~~~

On later runs, start the existing container with docker start attendance-mongo. You can also use a local MongoDB service or Atlas.

Create a Python virtual environment, install the dependencies, and start the API:

~~~powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

$env:MONGO_URI = "mongodb://127.0.0.1:27017"
$env:MONGO_DB = "attendance_db"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000 --reload
~~~

Confirm the Python version is 3.11 or newer. For MongoDB Atlas, set MONGO_URI to your Atlas connection string instead. You can set MONGO_URI and MONGO_DB in a root .env file; shell environment variables take priority. Keep credentials out of Git.

The app creates its indexes on startup. Open these URLs while the server is running:

- http://127.0.0.1:8000/ — dashboard
- http://127.0.0.1:8000/docs — interactive API reference (Swagger UI)
- http://127.0.0.1:8000/health — MongoDB readiness check; success returns {"status":"ok"}

A new database has no employees. In /docs, use POST /employees to create an employee first; then you can record attendance from the dashboard or API. Press **Ctrl+C** in the terminal to stop the server.

## Code layout

All application code is kept in app/main.py to match the assignment's single-file requirement. The file is organized into sections for MongoDB configuration and indexes, request validation, attendance rules, aggregation pipelines, API endpoints, and the browser dashboard.

- requirements.txt lists the Python dependencies.
- REVIEW.md records the starter-code review.
- DECISIONS.md explains the implementation choices.
