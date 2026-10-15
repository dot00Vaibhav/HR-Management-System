"""Employee Attendance & Analytics API. Run with uvicorn app.main:app --port 8000."""
import os
import re
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator
from pymongo import ASCENDING, DESCENDING, MongoClient, ReturnDocument
from pymongo.errors import DuplicateKeyError
from bson import json_util
import json

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"), serverSelectionTimeoutMS=3000, tz_aware=True)
db = client[os.getenv("MONGO_DB", "attendance_db")]
UTC = timezone.utc
IST = timezone(timedelta(hours=5, minutes=30))
PRESENCE = ("PRESENT", "WFH", "ON_DUTY")
STATUSES = (*PRESENCE, "ABSENT", "LEAVE")
app = FastAPI(title="Employee Attendance & Analytics API", version="2.0.0")

INDEX_HTML = r'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Employee attendance, punch records, and monthly team analytics.">
  <meta name="theme-color" content="#101d32"><title>Attendance Hub | HROne</title>
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <style>
    :root{color-scheme:light;--ink:#14243a;--muted:#64748b;--line:#e2e8f0;--brand:#176b58;--wash:#f5f8f7;--white:#fff;--danger:#a52626;--ok:#126847}
    *{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--wash);color:var(--ink);font:16px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif;overflow-x:hidden}
    a{color:inherit}button,input,select{font:inherit}button{cursor:pointer}.top{background:#101d32;color:white}.nav{max-width:1180px;margin:auto;min-height:72px;padding:12px 24px;display:flex;align-items:center;justify-content:space-between;gap:20px}
    .logo{text-decoration:none;font-weight:800;font-size:1.13rem;letter-spacing:.02em;display:flex;align-items:center;gap:10px}.logo-mark{width:34px;height:34px;border-radius:11px;background:#63d1a5;color:#10293a;display:grid;place-items:center;font-weight:900}
    .nav-links{display:flex;gap:24px}.nav-links a{text-decoration:none;color:#d9e4ee}.nav-links a:hover{color:#80e0b5}.menu{display:none;border:1px solid #66758a;color:white;background:transparent;border-radius:8px;padding:7px 11px}
    main{max-width:1180px;margin:0 auto;padding:34px 24px 64px}.hero{display:flex;align-items:flex-end;justify-content:space-between;gap:20px;margin-bottom:26px}.eyebrow{color:var(--brand);font-size:.78rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase}.hero h1{font-size:clamp(2rem,5vw,3rem);line-height:1.1;margin:6px 0}.hero p{color:var(--muted);margin:8px 0 0}.badge{background:#e0f2e9;color:#155d48;border-radius:999px;padding:8px 13px;font-size:.86rem;font-weight:700;white-space:nowrap}
    .notice{min-height:0;margin:0 0 16px;padding:0;border-radius:10px}.notice:not(:empty){padding:12px 15px;background:#e4f4eb;color:var(--ok)}.notice.error{background:#fff0f0;color:var(--danger)}
    .grid{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:18px}.card{background:var(--white);border:1px solid var(--line);border-radius:16px;padding:20px;box-shadow:0 5px 18px #14243a08;min-width:0}.span-8{grid-column:span 8}.span-4{grid-column:span 4}.span-6{grid-column:span 6}.span-12{grid-column:span 12}.card h2{font-size:1.12rem;margin:0 0 16px}.form-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.field{display:flex;flex-direction:column;gap:5px;min-width:0}.field.full{grid-column:1/-1}.field label{font-size:.85rem;font-weight:700}.field input,.field select{width:100%;min-width:0;padding:10px 11px;border:1px solid #cbd5e1;border-radius:9px;background:white;color:var(--ink)}.field input:focus,.field select:focus{outline:3px solid #a7ead0;border-color:var(--brand)}
    .actions{display:flex;flex-wrap:wrap;align-items:center;gap:9px;margin-top:14px}.btn{border:0;border-radius:9px;padding:10px 15px;background:var(--brand);color:white;font-weight:750}.btn:hover{background:#105544}.btn.secondary{background:#e8eef2;color:var(--ink)}.btn.secondary:hover{background:#d9e3e8}.inline{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.inline input{padding:9px;border:1px solid #cbd5e1;border-radius:8px;min-width:0;max-width:100%}.table-wrap{max-width:100%;overflow-x:auto}table{width:100%;border-collapse:collapse;text-align:left;font-size:.92rem}th,td{padding:11px 10px;border-bottom:1px solid var(--line);vertical-align:top}th{font-size:.77rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}td{overflow-wrap:anywhere}.empty{color:var(--muted);padding:14px 0}.metric{font-size:1.65rem;font-weight:800}.muted{color:var(--muted);font-size:.9rem}.footer{background:#101d32;color:#d9e4ee;padding:20px 24px}.footer-inner{max-width:1180px;margin:auto;display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}.footer a,.table-wrap a{color:#80e0b5}
    @media(max-width:760px){.nav{padding:12px 18px}.menu{display:block}.nav-links{display:none;position:absolute;z-index:3;left:0;right:0;top:66px;background:#101d32;padding:12px 20px 18px;flex-direction:column;gap:0;border-top:1px solid #334155}.nav-links.open{display:flex}.nav-links a{padding:10px 0}.hero{align-items:flex-start;flex-direction:column}main{padding:25px 16px 48px}.span-8,.span-4,.span-6{grid-column:span 12}.grid{gap:14px}.card{padding:17px}.badge{white-space:normal}.table-wrap{overflow:visible}table,thead,tbody,tr,td{display:block;width:100%}thead{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}tbody tr{padding:7px 0;border-bottom:1px solid var(--line)}td{display:grid;grid-template-columns:minmax(96px,34%) minmax(0,1fr);gap:10px;padding:6px 2px;border:0}td::before{content:attr(data-label);font-size:.77rem;font-weight:750;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}}
    @media(max-width:420px){.form-grid{grid-template-columns:1fr}.field.full{grid-column:auto}.inline{align-items:stretch}.inline input{flex:1 1 130px}.actions .btn{flex:1 1 auto}}
  </style>
</head>
<body>
  <header class="top" id="top"><nav class="nav" aria-label="Main navigation"><a class="logo" href="/" aria-label="Attendance Hub home"><span class="logo-mark" aria-hidden="true">H</span><span>Attendance Hub</span></a>
    <button id="menuButton" class="menu" type="button" aria-expanded="false" aria-controls="navLinks">Menu</button>
    <div id="navLinks" class="nav-links"><a href="#employees">Employees</a><a href="#attendance">Attendance</a><a href="#analytics">Analytics</a></div>
  </nav></header>
  <main>
    <section class="hero"><div><div class="eyebrow">People operations</div><h1>Attendance overview</h1><p>Manage employee records, daily punches, and team summaries.</p></div><div class="badge">All attendance times are in IST</div></section>
    <div id="notice" class="notice" role="status" aria-live="polite"></div>
    <div class="grid">
      <section class="card span-8" id="employees"><h2>Employees</h2><form id="employeeForm" class="form-grid">
        <div class="field"><label for="emp_code">Employee code</label><input id="emp_code" name="emp_code" pattern="EMP[0-9]{4,6}" required></div>
        <div class="field"><label for="name">Full name</label><input id="name" name="name" maxlength="100" required></div>
        <div class="field"><label for="email">Work email</label><input id="email" name="email" type="email" maxlength="120" required></div>
        <div class="field"><label for="department">Department</label><input id="department" name="department" maxlength="50" required></div>
        <div class="field"><label for="joined_on">Joined on</label><input id="joined_on" name="joined_on" type="date" required></div>
        <div class="field"><label for="shift_start">Shift start (IST)</label><input id="shift_start" name="shift_start" type="time" value="09:30" required></div>
        <div class="field"><label for="shift_end">Shift end (IST)</label><input id="shift_end" name="shift_end" type="time" value="18:30" required></div>
        <div class="field full"><button class="btn" type="submit">Add employee</button></div>
      </form></section>
      <section class="card span-4"><h2>Quick punch</h2><div class="field"><label for="punchCode">Employee code</label><input id="punchCode" pattern="EMP[0-9]{4,6}"></div>
        <div class="field" style="margin-top:12px"><label for="punchStatus">Punch-in status</label><select id="punchStatus"><option>PRESENT</option><option>WFH</option><option>ON_DUTY</option></select></div>
        <div class="actions"><button class="btn" id="punchIn" type="button">Punch in</button><button class="btn secondary" id="punchOut" type="button">Punch out</button></div>
        <p class="muted">The API uses the current time when no timestamp is supplied.</p></section>
      <section class="card span-6"><h2>Manual correction</h2><form id="correctionForm" class="form-grid">
        <div class="field"><label for="correctionCode">Employee code</label><input id="correctionCode" required></div><div class="field"><label for="correctionDate">Attendance date</label><input id="correctionDate" type="date" required></div>
        <div class="field"><label for="correctionStatus">Status</label><select id="correctionStatus"><option value="">Keep current</option><option>PRESENT</option><option>WFH</option><option>ON_DUTY</option><option>ABSENT</option><option>LEAVE</option></select></div>
        <div class="field"><label for="correctionPin">Punch in (IST, optional)</label><input id="correctionPin" type="datetime-local"></div><div class="field"><label for="correctionPout">Punch out (IST, optional)</label><input id="correctionPout" type="datetime-local"></div>
        <div class="field"><label for="correctionBy">Corrected by</label><input id="correctionBy" maxlength="50" required></div><div class="field full"><label for="correctionReason">Reason</label><input id="correctionReason" minlength="5" maxlength="200" required></div>
        <div class="field full"><button class="btn" type="submit">Save correction</button></div></form></section>
      <section class="card span-12"><div class="inline" style="justify-content:space-between;margin-bottom:10px"><h2 style="margin:0">Employee directory</h2><button id="reloadEmployees" class="btn secondary" type="button">Refresh</button></div><div id="employeeTable" class="table-wrap"></div></section>
      <section class="card span-12" id="attendance"><div class="inline" style="justify-content:space-between;margin-bottom:10px"><h2 style="margin:0">Recent attendance</h2><button id="reloadAttendance" class="btn secondary" type="button">Refresh</button></div><div id="attendanceTable" class="table-wrap"></div></section>
      <section class="card span-6" id="analytics"><h2>Employee monthly summary</h2><form id="employeeAnalytics" class="form-grid">
        <div class="field"><label for="summaryCode">Employee code</label><input id="summaryCode" required></div><div class="field"><label for="summaryMonth">Month</label><input id="summaryMonth" type="month" required></div>
        <div class="field full"><button class="btn" type="submit">View summary</button></div></form><div id="employeeSummary" class="muted" style="margin-top:14px">Choose an employee and month to load the summary.</div></section>
      <section class="card span-6"><h2>Department summary</h2><form id="departmentAnalytics" class="form-grid">
        <div class="field"><label for="departmentMonth">Month</label><input id="departmentMonth" type="month" required></div><div class="field"><label for="departmentFilter">Department (optional)</label><input id="departmentFilter"></div>
        <div class="field full"><button class="btn" type="submit">View departments</button></div></form><div id="departmentSummary" class="table-wrap" style="margin-top:14px"></div></section>
      <section class="card span-6"><h2>Late leaderboard</h2><form id="leaderboardForm" class="form-grid"><div class="field"><label for="leaderMonth">Month</label><input id="leaderMonth" type="month" required></div>
        <div class="field"><label for="leaderDepartment">Department (optional)</label><input id="leaderDepartment"></div><div class="field"><label for="leaderLimit">Rank limit</label><input id="leaderLimit" type="number" min="1" max="50" value="10" required></div>
        <div class="field full"><button class="btn" type="submit">View leaderboard</button></div></form><div id="leaderboardTable" class="table-wrap" style="margin-top:14px"></div></section>
      <section class="card span-6"><h2>Department trend</h2><form id="trendForm" class="form-grid"><div class="field"><label for="trendDepartment">Department</label><input id="trendDepartment" required></div><div class="field"><label for="trendFrom">From</label><input id="trendFrom" type="date" required></div>
        <div class="field"><label for="trendTo">To (max 92 days)</label><input id="trendTo" type="date" required></div><div class="field full"><button class="btn" type="submit">View trend</button></div></form><div id="trendTable" class="table-wrap" style="margin-top:14px"></div></section>
    </div>
  </main>
  <footer class="footer"><div class="footer-inner"><span>© <span id="year"></span> Attendance Hub</span><a href="#top" aria-label="Back to top">Back to top ↑</a></div></footer>
  <script>
    const $=id=>document.getElementById(id), notice=$('notice');
    $('year').textContent=new Date().getFullYear();
    $('menuButton').addEventListener('click',()=>{const open=$('navLinks').classList.toggle('open');$('menuButton').setAttribute('aria-expanded',String(open));});
    $('navLinks').addEventListener('click',e=>{if(e.target.closest('a')){$('navLinks').classList.remove('open');$('menuButton').setAttribute('aria-expanded','false');}});
    const show=(text,error=false)=>{notice.textContent=text;notice.classList.toggle('error',error);window.scrollTo({top:0,behavior:'smooth'});};
    async function api(path,options={}){const response=await fetch(path,{...options,headers:{'Accept':'application/json','Content-Type':'application/json',...(options.headers||{})}});let data;try{data=await response.json()}catch{data={detail:'Unexpected server response'}}if(!response.ok){const detail=Array.isArray(data.detail)?data.detail.map(x=>x.msg).join('; '):data.detail;throw Error(detail||`Request failed (${response.status})`)}return data;}
    function table(target,columns,rows){const root=$(target);root.replaceChildren();if(!rows.length){root.textContent='No records found.';root.className='empty';return}root.className='table-wrap';const t=document.createElement('table'),head=document.createElement('thead'),tr=document.createElement('tr');columns.forEach(c=>{const th=document.createElement('th');th.textContent=c.label;tr.append(th)});head.append(tr);t.append(head);const body=document.createElement('tbody');rows.forEach(row=>{const r=document.createElement('tr');columns.forEach(c=>{const td=document.createElement('td');td.dataset.label=c.label;const value=c.get(row);if(value===null||value===undefined){td.textContent='—'}else if(c.href){const a=document.createElement('a');a.href=c.href(value,row);a.textContent=String(value);td.append(a)}else{td.textContent=String(value)}r.append(td)});body.append(r)});t.append(body);root.append(t)}
    const timeText=ms=>ms?new Date(ms).toLocaleString():'—';
    async function loadEmployees(){const d=await api('/employees?page=1&page_size=100');table('employeeTable',[{label:'Code',get:r=>r.emp_code},{label:'Name',get:r=>r.name},{label:'Department',get:r=>r.department},{label:'Email',get:r=>r.email,href:v=>`mailto:${v}`},{label:'Joined',get:r=>r.joined_on}],d.items)}
    async function loadAttendance(){const d=await api('/attendance?page=1&page_size=20');table('attendanceTable',[{label:'Date',get:r=>r.date},{label:'Code',get:r=>r.emp_code},{label:'Status',get:r=>r.status},{label:'Punch in',get:r=>timeText(r.punch_in)},{label:'Punch out',get:r=>timeText(r.punch_out)},{label:'Hours',get:r=>r.work_hours}],d.items)}
    $('employeeForm').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.currentTarget),data=Object.fromEntries(f.entries());try{await api('/employees',{method:'POST',body:JSON.stringify(data)});e.currentTarget.reset();$('shift_start').value='09:30';$('shift_end').value='18:30';show('Employee added.');await loadEmployees()}catch(err){show(err.message,true)}});
    $('punchIn').addEventListener('click',async()=>{try{const code=$('punchCode').value.trim();if(!code)throw Error('Enter an employee code.');await api('/attendance/punch-in',{method:'POST',body:JSON.stringify({emp_code:code,status:$('punchStatus').value})});show('Punch-in recorded.');await loadAttendance()}catch(err){show(err.message,true)}});
    $('punchOut').addEventListener('click',async()=>{try{const code=$('punchCode').value.trim();if(!code)throw Error('Enter an employee code.');await api('/attendance/punch-out',{method:'POST',body:JSON.stringify({emp_code:code})});show('Punch-out recorded.');await loadAttendance()}catch(err){show(err.message,true)}});
    $('correctionForm').addEventListener('submit',async e=>{e.preventDefault();try{const code=$('correctionCode').value.trim(),day=$('correctionDate').value,body={reason:$('correctionReason').value,regularized_by:$('correctionBy').value};if($('correctionStatus').value)body.status=$('correctionStatus').value;for(const [field,key] of [['correctionPin','punch_in'],['correctionPout','punch_out']]){const value=$(field).value;if(value)body[key]=new Date(value+':00+05:30').getTime()}await api(`/attendance/${encodeURIComponent(code)}/${encodeURIComponent(day)}`,{method:'PATCH',body:JSON.stringify(body)});e.currentTarget.reset();show('Correction saved with an audit entry.');await loadAttendance()}catch(err){show(err.message,true)}});
    $('reloadEmployees').addEventListener('click',()=>loadEmployees().then(()=>show('Employee list refreshed.')).catch(e=>show(e.message,true)));
    $('reloadAttendance').addEventListener('click',()=>loadAttendance().then(()=>show('Attendance refreshed.')).catch(e=>show(e.message,true)));
    $('employeeAnalytics').addEventListener('submit',async e=>{e.preventDefault();try{const d=await api(`/analytics/employees/${encodeURIComponent($('summaryCode').value.trim())}/monthly?month=${encodeURIComponent($('summaryMonth').value)}`);$('employeeSummary').textContent=`${d.month}: ${d.present_days} present days · ${d.working_days} working days · ${d.attendance_pct??'—'}% attendance · ${d.late_count} late days`;show('Employee summary loaded.')}catch(err){show(err.message,true)}});
    $('departmentAnalytics').addEventListener('submit',async e=>{e.preventDefault();try{const p=new URLSearchParams({month:$('departmentMonth').value});if($('departmentFilter').value.trim())p.set('department',$('departmentFilter').value.trim());const d=await api(`/analytics/departments/summary?${p}`);table('departmentSummary',[{label:'Department',get:r=>r.department},{label:'Headcount',get:r=>r.headcount},{label:'Present days',get:r=>r.present_days},{label:'Avg hours',get:r=>r.avg_work_hours},{label:'Late',get:r=>r.late_count}],d.items);show('Department summary loaded.')}catch(err){show(err.message,true)}});
    $('leaderboardForm').addEventListener('submit',async e=>{e.preventDefault();try{const p=new URLSearchParams({month:$('leaderMonth').value,limit:$('leaderLimit').value});if($('leaderDepartment').value.trim())p.set('department',$('leaderDepartment').value.trim());const d=await api(`/analytics/leaderboard/late?${p}`);table('leaderboardTable',[{label:'Rank',get:r=>r.rank},{label:'Employee',get:r=>`${r.name} (${r.emp_code})`},{label:'Department',get:r=>r.department},{label:'Late minutes',get:r=>r.total_late_minutes},{label:'Late days',get:r=>r.late_count}],d.items);show('Leaderboard loaded.')}catch(err){show(err.message,true)}});
    $('trendForm').addEventListener('submit',async e=>{e.preventDefault();try{const dept=encodeURIComponent($('trendDepartment').value.trim()),p=new URLSearchParams({from:$('trendFrom').value,to:$('trendTo').value});const d=await api(`/analytics/departments/${dept}/trend?${p}`);table('trendTable',[{label:'Date',get:r=>r.date},{label:'Working day',get:r=>r.is_working_day?'Yes':'No'},{label:'Headcount',get:r=>r.headcount},{label:'Present',get:r=>r.present_count},{label:'Rate',get:r=>r.attendance_rate},{label:'7-day avg',get:r=>r.moving_avg_7d}],d.items);show('Department trend loaded.')}catch(err){show(err.message,true)}});
    Promise.all([loadEmployees(),loadAttendance()]).catch(e=>show(e.message,true));
  </script>
</body></html>'''


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home():
    return HTMLResponse(INDEX_HTML)


@app.get("/favicon.svg", include_in_schema=False)
def favicon():
    return Response(content='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="18" fill="#63d1a5"/><path d="M18 15h8v14h12V15h8v34h-8V36H26v13h-8z" fill="#10293a"/></svg>', media_type="image/svg+xml")


@app.exception_handler(404)
async def custom_not_found(request: Request, exc):
    if "text/html" in request.headers.get("accept", ""):
        page = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="This page could not be found."><title>Page not found | Attendance Hub</title><link rel="icon" href="/favicon.svg" type="image/svg+xml"><style>body{margin:0;min-height:100vh;display:grid;place-items:center;padding:24px;background:#f5f8f7;color:#14243a;font:16px/1.5 system-ui,sans-serif;text-align:center}.box{max-width:460px}h1{font-size:clamp(2rem,9vw,4rem);margin:0;color:#176b58}p{color:#64748b}a{display:inline-block;margin-top:12px;background:#176b58;color:white;padding:11px 18px;border-radius:9px;text-decoration:none;font-weight:700}</style></head><body><main class="box"><h1>404</h1><h2>Page not found</h2><p>The link may be outdated, or the address may be incorrect.</p><a href="/">Return to Attendance Hub</a></main></body></html>'''
        return HTMLResponse(page, status_code=404)
    return JSONResponse({"detail": getattr(exc, "detail", "Not found")}, status_code=404)


@app.on_event("startup")
def ensure_indexes():
    db.employees.create_index([("emp_code", ASCENDING)], unique=True, name="uq_employee_code")
    db.employees.create_index([("department", ASCENDING), ("emp_code", ASCENDING)], name="ix_employee_department_code")
    db.employees.create_index([("department", ASCENDING), ("joined_on", ASCENDING)], name="ix_employee_department_joined")
    db.employees.create_index([("joined_on", ASCENDING)], name="ix_employee_joined")
    db.attendance_logs.create_index([("emp_code", ASCENDING), ("date", ASCENDING)], unique=True, name="uq_attendance_employee_date")
    db.attendance_logs.create_index([("date", DESCENDING), ("emp_code", ASCENDING)], name="ix_attendance_date_employee")
    db.attendance_logs.create_index([("date", ASCENDING), ("emp_code", ASCENDING), ("status", ASCENDING)], name="ix_attendance_date_code_status")
    db.attendance_logs.create_index([("emp_code", ASCENDING), ("punch_in", DESCENDING)], name="ix_attendance_punch_in")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="ignore")


def valid_date(value: str) -> str:
    try:
        parsed = date.fromisoformat(value)
    except (ValueError, TypeError):
        raise HTTPException(422, "date must be YYYY-MM-DD")
    if parsed.isoformat() != value:
        raise HTTPException(422, "date must be YYYY-MM-DD")
    return value


def valid_instant(value: int | None) -> int | None:
    if value is None:
        return None
    if not 100_000_000_000 <= value <= 4_102_444_800_000:
        raise ValueError("timestamp must be epoch milliseconds")
    return value


def millis_to_dt(ms: int) -> datetime:
    return datetime(1970, 1, 1, tzinfo=UTC) + timedelta(milliseconds=ms - (ms % 1000))


def dt_to_millis(value: datetime | None) -> int | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return int(value.timestamp() * 1000)


def serial_dt(value):
    return dt_to_millis(value) if isinstance(value, datetime) else value


def public_record(doc: dict) -> dict:
    result = {k: v for k, v in doc.items() if k != "_id"}
    for k in ("punch_in", "punch_out"):
        result[k] = serial_dt(result.get(k))
    result["history"] = result.get("history") or []
    for item in result["history"]:
        item["at"] = serial_dt(item.get("at"))
        for change in item.get("changes", {}).values():
            change["from"] = serial_dt(change.get("from"))
            change["to"] = serial_dt(change.get("to"))
    result.setdefault("late_minutes", 0)
    result.setdefault("overtime_minutes", 0)
    result.setdefault("half_day", False)
    result.setdefault("work_hours", None)
    return result


def public_employee(doc: dict) -> dict:
    result = {k: v for k, v in doc.items() if k != "_id"}
    result["created_at"] = serial_dt(result.get("created_at"))
    return result


def hm(s: str) -> time:
    if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", s):
        raise ValueError("time must be HH:MM")
    h, m = map(int, s.split(":"))
    return time(h, m)


def trunc_seconds(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).replace(microsecond=0)


def shift_bounds(emp: dict, punch: datetime, attendance_date: str | None = None) -> tuple[datetime, datetime]:
    local = punch.astimezone(IST)
    start_t, end_t = hm(emp["shift_start"]), hm(emp["shift_end"])
    d = date.fromisoformat(attendance_date) if attendance_date else local.date()
    overnight = end_t <= start_t
    if attendance_date is None and overnight and local.timetz().replace(tzinfo=None) < end_t:
        d -= timedelta(days=1)
    start_local = datetime.combine(d, start_t, IST)
    end_local = datetime.combine(d + (timedelta(days=1) if overnight else timedelta()), end_t, IST)
    return start_local.astimezone(UTC), end_local.astimezone(UTC)


def attendance_day(emp: dict, punch: datetime) -> str:
    local = punch.astimezone(IST)
    if hm(emp["shift_end"]) <= hm(emp["shift_start"]) and local.timetz().replace(tzinfo=None) < hm(emp["shift_end"]):
        local -= timedelta(days=1)
    return local.date().isoformat()


def derived(emp: dict, status: str, punch_in: datetime | None, punch_out: datetime | None, day: str) -> dict:
    if status not in PRESENCE:
        return {"work_hours": None, "late_minutes": 0, "overtime_minutes": 0, "half_day": False}
    if punch_in is None:
        raise HTTPException(422, "presence status requires punch_in")
    start, end = shift_bounds(emp, punch_in, day)
    delay = int((punch_in - start).total_seconds() // 60)
    late = delay if (punch_in - start).total_seconds() > 600 else 0
    if punch_out is None:
        return {"work_hours": None, "late_minutes": late, "overtime_minutes": 0, "half_day": False}
    seconds = int((punch_out - punch_in).total_seconds())
    hours = float((Decimal(seconds) / Decimal(3600)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    over = int((punch_out - end).total_seconds() // 60)
    return {"work_hours": hours, "late_minutes": late, "overtime_minutes": over if over >= 30 else 0, "half_day": hours < 4.5}


class EmployeeIn(StrictModel):
    emp_code: str = Field(pattern=r"^EMP\d{4,6}$")
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(max_length=120, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    department: str = Field(min_length=1, max_length=50)
    shift_start: str = "09:30"
    shift_end: str = "18:30"
    joined_on: str
    @field_validator("shift_start", "shift_end")
    @classmethod
    def shift_time(cls, v): hm(v); return v
    @field_validator("joined_on")
    @classmethod
    def date_value(cls, v):
        try: return valid_date(v)
        except HTTPException as exc: raise ValueError(exc.detail)
    @model_validator(mode="after")
    def shifts_differ(self):
        if self.shift_start == self.shift_end: raise ValueError("shift_start and shift_end must differ")
        return self


class PunchInIn(StrictModel):
    emp_code: str
    punched_at: StrictInt | None = None
    status: Literal["PRESENT", "WFH", "ON_DUTY"] = "PRESENT"
    @model_validator(mode="before")
    @classmethod
    def reject_null_timestamp(cls, value):
        if isinstance(value, dict) and "punched_at" in value and value["punched_at"] is None:
            raise ValueError("punched_at must be omitted or an epoch-millisecond integer")
        return value
    @field_validator("punched_at")
    @classmethod
    def timestamp(cls, v): return valid_instant(v)


class PunchOutIn(StrictModel):
    emp_code: str
    punched_at: StrictInt | None = None
    @model_validator(mode="before")
    @classmethod
    def reject_null_timestamp(cls, value):
        if isinstance(value, dict) and "punched_at" in value and value["punched_at"] is None:
            raise ValueError("punched_at must be omitted or an epoch-millisecond integer")
        return value
    @field_validator("punched_at")
    @classmethod
    def timestamp(cls, v): return valid_instant(v)


class RegularizeIn(StrictModel):
    status: Literal["PRESENT", "WFH", "ON_DUTY", "ABSENT", "LEAVE"] | None = None
    punch_in: StrictInt | None = None
    punch_out: StrictInt | None = None
    reason: str = Field(min_length=5, max_length=200)
    regularized_by: str = Field(min_length=1, max_length=50)
    @model_validator(mode="before")
    @classmethod
    def reject_null_patch_values(cls, value):
        if isinstance(value, dict):
            for key in ("status", "punch_in", "punch_out"):
                if key in value and value[key] is None:
                    raise ValueError(f"{key} cannot be null")
        return value
    @field_validator("punch_in", "punch_out")
    @classmethod
    def timestamp(cls, v): return valid_instant(v)


def month_bounds(month: str):
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", month): raise HTTPException(422, "month must be YYYY-MM")
    first = date.fromisoformat(month + "-01")
    last = (date(first.year + (first.month == 12), first.month % 12 + 1, 1) - timedelta(days=1))
    return first.isoformat(), last.isoformat(), last


def rounded(value: float, places: int = 2) -> float:
    quantum = Decimal("1").scaleb(-places)
    return float(Decimal(str(value)).quantize(quantum, rounding=ROUND_HALF_UP))


@app.get("/health")
def health():
    try: client.admin.command("ping")
    except Exception: raise HTTPException(503, "MongoDB unavailable")
    return {"status": "ok"}


@app.post("/employees", status_code=201)
def create_employee(body: EmployeeIn):
    doc = body.model_dump()
    doc["created_at"] = datetime.now(UTC).replace(microsecond=0)
    try: db.employees.insert_one(doc)
    except DuplicateKeyError: raise HTTPException(409, "emp_code already exists")
    return public_employee(doc)


@app.get("/employees")
def list_employees(department: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    q = {"department": department} if department is not None else {}
    total = db.employees.count_documents(q)
    items = [public_employee(d) for d in db.employees.find(q, {"_id": 0}).sort("emp_code", ASCENDING).skip((page-1)*page_size).limit(page_size)]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@app.post("/attendance/punch-in", status_code=201)
def punch_in(body: PunchInIn):
    emp = db.employees.find_one({"emp_code": body.emp_code})
    if not emp: raise HTTPException(404, "employee not found")
    ts = trunc_seconds(millis_to_dt(body.punched_at)) if body.punched_at is not None else datetime.now(UTC).replace(microsecond=0)
    day = attendance_day(emp, ts)
    doc = {"emp_code": body.emp_code, "date": day, "status": body.status, "punch_in": ts, "punch_out": None,
           "work_hours": None, "late_minutes": derived(emp, body.status, ts, None, day)["late_minutes"],
           "overtime_minutes": 0, "half_day": False, "history": []}
    try: db.attendance_logs.insert_one(doc)
    except DuplicateKeyError: raise HTTPException(409, "already punched in for this date")
    return public_record(doc)


def attendance_filter(emp_code=None, date_from=None, date_to=None, status=None):
    q = {}
    if emp_code is not None: q["emp_code"] = emp_code
    if date_from or date_to:
        q["date"] = {}
        if date_from: q["date"]["$gte"] = valid_date(date_from)
        if date_to: q["date"]["$lte"] = valid_date(date_to)
        if date_from and date_to and date_from > date_to: raise HTTPException(422, "date_from must not exceed date_to")
    if status is not None:
        if status not in STATUSES: raise HTTPException(422, "invalid status")
        q["status"] = status
    return q


@app.get("/attendance")
def list_attendance(emp_code: str | None = None, date_from: str | None = None, date_to: str | None = None,
                    status: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    q = attendance_filter(emp_code, date_from, date_to, status)
    total = db.attendance_logs.count_documents(q)
    docs = db.attendance_logs.find(q, {"_id": 0}).sort([("date", DESCENDING), ("emp_code", ASCENDING)]).skip((page-1)*page_size).limit(page_size)
    return {"items": [public_record(d) for d in docs], "total": total, "page": page, "page_size": page_size}


@app.post("/attendance/punch-out")
def punch_out(body: PunchOutIn):
    emp = db.employees.find_one({"emp_code": body.emp_code})
    if not emp: raise HTTPException(404, "employee not found")
    ts = trunc_seconds(millis_to_dt(body.punched_at)) if body.punched_at is not None else datetime.now(UTC).replace(microsecond=0)
    doc = db.attendance_logs.find_one({"emp_code": body.emp_code, "punch_in": {"$lte": ts}, "status": {"$in": PRESENCE}}, sort=[("punch_in", DESCENDING)])
    if not doc: raise HTTPException(404, "no punch-in found")
    pi = trunc_seconds(doc["punch_in"])
    seconds = (ts-pi).total_seconds()
    if seconds <= 0 or seconds > 86400: raise HTTPException(422, "punch_out must be after punch_in and within 24 hours")
    values = derived(emp, doc["status"], pi, ts, doc["date"])
    updated = db.attendance_logs.find_one_and_update({"_id": doc["_id"], "punch_out": None},
        {"$set": {"punch_in": pi, "punch_out": ts, **values}}, return_document=ReturnDocument.AFTER)
    if updated is None: raise HTTPException(409, "record is already punched out")
    return public_record(updated)


@app.patch("/attendance/{emp_code}/{date}")
def regularize(emp_code: str, date: str, body: RegularizeIn):
    valid_date(date)
    emp = db.employees.find_one({"emp_code": emp_code})
    if not emp: raise HTTPException(404, "employee not found")
    old = db.attendance_logs.find_one({"emp_code": emp_code, "date": date})
    if not old: raise HTTPException(404, "attendance record not found")
    status = body.status if body.status is not None else old["status"]
    if status in ("ABSENT", "LEAVE") and (body.punch_in is not None or body.punch_out is not None):
        raise HTTPException(422, "ABSENT and LEAVE cannot have punch times")
    pin = millis_to_dt(body.punch_in) if body.punch_in is not None else old.get("punch_in")
    pout = millis_to_dt(body.punch_out) if body.punch_out is not None else old.get("punch_out")
    if status in ("ABSENT", "LEAVE"): pin = pout = None
    if status in PRESENCE and pin is None: raise HTTPException(422, "presence status requires punch_in")
    if pin is not None and attendance_day(emp, pin) != date: raise HTTPException(422, "punch_in must belong to attendance date")
    if pout is not None:
        if pin is None or pout <= pin or (pout-pin).total_seconds() > 86400: raise HTTPException(422, "invalid punch_out")
        pout = trunc_seconds(pout)
    if pin is not None: pin = trunc_seconds(pin)
    computed = derived(emp, status, pin, pout, date)
    final = {"status": status, "punch_in": pin, "punch_out": pout, **computed}
    changed = {}
    for key, value in final.items():
        prior = old.get(key)
        if isinstance(prior, datetime): prior = trunc_seconds(prior)
        if prior != value: changed[key] = {"from": prior, "to": value}
    if not changed: raise HTTPException(422, "request does not change the record")
    entry = {"at": datetime.now(UTC).replace(microsecond=0), "by": body.regularized_by, "reason": body.reason, "changes": changed}
    history_guard = {"history": old["history"]} if "history" in old else {"history": {"$exists": False}}
    updated = db.attendance_logs.find_one_and_update({"_id": old["_id"], **history_guard},
        {"$set": final, "$push": {"history": entry}}, return_document=ReturnDocument.AFTER)
    if updated is None: raise HTTPException(409, "record changed concurrently")
    return public_record(updated)


def employee_month_pipeline(emp_code: str, month: str):
    start, end, last = month_bounds(month)
    return [{"$match": {"emp_code": emp_code, "date": {"$gte": start, "$lte": end}}},
      {"$addFields": {"_weekday": {"$dayOfWeek": {"$dateFromString": {"dateString": "$date"}}}}},
      {"$group": {"_id": None,
       "present_days": {"$sum": {"$cond": [{"$and": [{"$in": ["$status", list(PRESENCE)]}, {"$in": ["$_weekday", [2,3,4,5,6]]}]}, {"$cond": [{"$eq": [{"$ifNull": ["$half_day", False]}, True]}, 0.5, 1]}, 0]}},
       "leave_days": {"$sum": {"$cond": [{"$eq": ["$status", "LEAVE"]}, 1, 0]}},
       "late_count": {"$sum": {"$cond": [{"$gt": [{"$ifNull": ["$late_minutes", 0]}, 0]}, 1, 0]}},
       "total_late_minutes": {"$sum": {"$ifNull": ["$late_minutes", 0]}},
       "total_overtime_minutes": {"$sum": {"$ifNull": ["$overtime_minutes", 0]}}}}]


def employee_working_days_pipeline(emp_code: str, month: str):
    start, end, _ = month_bounds(month)
    start_date = {"$dateFromString": {"dateString": "$effective_start"}}
    end_date = {"$dateFromString": {"dateString": end}}
    count = {"$cond": [{"$lte": [start_date, end_date]}, {"$add": [{"$dateDiff": {"startDate": start_date, "endDate": end_date, "unit": "day"}}, 1]}, 0]}
    return [{"$match": {"emp_code": emp_code}},
      {"$project": {"effective_start": {"$cond": [{"$gt": ["$joined_on", start]}, "$joined_on", start]}}},
      {"$project": {"days": {"$map": {"input": {"$range": [0, count]}, "as": "offset", "in": {"$dateAdd": {"startDate": start_date, "unit": "day", "amount": "$$offset"}}}}}},
      {"$project": {"working_days": {"$size": {"$filter": {"input": "$days", "as": "day", "cond": {"$in": [{"$dayOfWeek": "$$day"}, [2, 3, 4, 5, 6]]}}}}}}]


@app.get("/analytics/employees/{emp_code}/monthly")
def employee_monthly(emp_code: str, month: str):
    start, end, _ = month_bounds(month)
    emp = db.employees.find_one({"emp_code": emp_code}, {"_id": 1, "joined_on": 1})
    if not emp: raise HTTPException(404, "employee not found")
    result = list(db.attendance_logs.aggregate(employee_month_pipeline(emp_code, month)))
    row = result[0] if result else {}
    work_days = list(db.employees.aggregate(employee_working_days_pipeline(emp_code, month)))
    wd = work_days[0]["working_days"] if work_days else 0
    present = rounded(float(row.get("present_days", 0)))
    return {"emp_code": emp_code, "month": month, "working_days": wd, "present_days": present,
      "leave_days": row.get("leave_days", 0), "late_count": row.get("late_count", 0),
      "total_late_minutes": row.get("total_late_minutes", 0), "total_overtime_minutes": row.get("total_overtime_minutes", 0),
      "attendance_pct": rounded(present/wd*100) if wd else None}


def dept_summary_pipeline(month: str, department: str | None):
    start, end, last = month_bounds(month)
    match = {"joined_on": {"$lte": last.isoformat()}}
    if department is not None: match["department"] = department
    return [{"$match": match}, {"$lookup": {"from": "attendance_logs", "let": {"code": "$emp_code"}, "pipeline": [
      {"$match": {"$expr": {"$and": [{"$eq": ["$emp_code", "$$code"]}, {"$gte": ["$date", start]}, {"$lte": ["$date", end]}]}}}], "as": "logs"}},
      {"$unwind": {"path": "$logs", "preserveNullAndEmptyArrays": True}},
      {"$group": {"_id": {"department": "$department", "emp_code": "$emp_code"}, "headcount": {"$first": 1},
       "present_days": {"$sum": {"$cond": [{"$and": [{"$in": ["$logs.status", list(PRESENCE)]}, {"$in": [{"$dayOfWeek": {"$dateFromString": {"dateString": "$logs.date"}}}, [2,3,4,5,6]]}]}, {"$cond": [{"$eq": [{"$ifNull": ["$logs.half_day", False]}, True]}, 0.5, 1]}, 0]}},
       "work_hours_sum": {"$sum": {"$cond": [{"$and": [{"$in": ["$logs.status", list(PRESENCE)]}, {"$ne": ["$logs.work_hours", None]}]}, "$logs.work_hours", 0]}},
       "work_hours_count": {"$sum": {"$cond": [{"$and": [{"$in": ["$logs.status", list(PRESENCE)]}, {"$ne": ["$logs.work_hours", None]}]}, 1, 0]}},
       "late_count": {"$sum": {"$cond": [{"$gt": [{"$ifNull": ["$logs.late_minutes", 0]}, 0]}, 1, 0]}},
       "total_late_minutes": {"$sum": {"$ifNull": ["$logs.late_minutes", 0]}},
       "leave_count": {"$sum": {"$cond": [{"$eq": ["$logs.status", "LEAVE"]}, 1, 0]}},
       "on_duty_count": {"$sum": {"$cond": [{"$eq": ["$logs.status", "ON_DUTY"]}, 1, 0]}}}},
      {"$group": {"_id": "$_id.department", "headcount": {"$sum": "$headcount"}, "present_days": {"$sum": "$present_days"},
        "work_hours_sum": {"$sum": "$work_hours_sum"}, "work_hours_count": {"$sum": "$work_hours_count"}, "late_count": {"$sum": "$late_count"},
        "total_late_minutes": {"$sum": "$total_late_minutes"}, "leave_count": {"$sum": "$leave_count"}, "on_duty_count": {"$sum": "$on_duty_count"}}},
      {"$match": {"headcount": {"$gt": 0}}}, {"$project": {"_id": 0, "department": "$_id", "headcount": 1, "present_days": 1,
        "avg_work_hours": {"$cond": [{"$gt": ["$work_hours_count", 0]}, {"$divide": ["$work_hours_sum", "$work_hours_count"]}, None]},
        "late_count": 1, "total_late_minutes": 1, "leave_count": 1, "on_duty_count": 1}}, {"$sort": {"department": 1}}]


@app.get("/analytics/departments/summary")
def department_summary(month: str, department: str | None = None):
    month_bounds(month)
    rows = list(db.employees.aggregate(dept_summary_pipeline(month, department), allowDiskUse=True))
    for r in rows:
        r["present_days"] = rounded(float(r["present_days"]))
        if r["avg_work_hours"] is not None: r["avg_work_hours"] = rounded(float(r["avg_work_hours"]))
    return {"month": month, "items": rows}


def leaderboard_pipeline(month: str, department: str | None, limit: int):
    start, end, _ = month_bounds(month)
    stages = [{"$match": {"date": {"$gte": start, "$lte": end}, "late_minutes": {"$gt": 0}}},
      {"$group": {"_id": "$emp_code", "total_late_minutes": {"$sum": "$late_minutes"}, "late_count": {"$sum": 1}}},
      {"$lookup": {"from": "employees", "localField": "_id", "foreignField": "emp_code", "as": "employee"}}, {"$unwind": "$employee"}]
    if department is not None: stages.append({"$match": {"employee.department": department}})
    stages += [{"$setWindowFields": {"sortBy": {"total_late_minutes": -1}, "output": {"rank": {"$rank": {}}}}},
      {"$match": {"rank": {"$lte": limit}}},
      {"$sort": {"total_late_minutes": -1, "_id": 1}}, {"$project": {"_id": 0, "rank": 1, "emp_code": "$_id", "name": "$employee.name", "department": "$employee.department", "total_late_minutes": 1, "late_count": 1}}]
    return stages


@app.get("/analytics/leaderboard/late")
def late_leaderboard(month: str, limit: int = Query(10, ge=1, le=50), department: str | None = None):
    month_bounds(month)
    rows = list(db.attendance_logs.aggregate(leaderboard_pipeline(month, department, limit), allowDiskUse=True))
    return {"month": month, "items": rows}


def trend_pipeline(department: str, start: str, end: str):
    # Seed the date series from a department employee, so even a department with
    # no logs on any requested date still gets one row per day after densifying.
    return [{"$match": {"department": department}}, {"$limit": 1},
      {"$project": {"_id": {"$dateFromString": {"dateString": start}}}},
      {"$densify": {"field": "_id", "range": {"step": 1, "unit": "day", "bounds": [datetime.fromisoformat(start), datetime.fromisoformat(end) + timedelta(days=1)]}}},
      {"$set": {"date": {"$dateToString": {"date": "$_id", "format": "%Y-%m-%d"}}, "is_working_day": {"$in": [{"$dayOfWeek": "$_id"}, [2,3,4,5,6]]}}},
      {"$lookup": {"from": "attendance_logs", "let": {"d": "$date"}, "pipeline": [
        {"$match": {"$expr": {"$eq": ["$date", "$$d"]}}},
        {"$lookup": {"from": "employees", "localField": "emp_code", "foreignField": "emp_code", "as": "employee"}},
        {"$unwind": "$employee"}, {"$match": {"employee.department": department}},
        {"$group": {"_id": None, "present_count": {"$sum": {"$cond": [{"$in": ["$status", list(PRESENCE)]}, {"$cond": [{"$eq": [{"$ifNull": ["$half_day", False]}, True]}, 0.5, 1]}, 0]}},
          "late_count": {"$sum": {"$cond": [{"$gt": [{"$ifNull": ["$late_minutes", 0]}, 0]}, 1, 0]}}}}], "as": "daily"}},
      {"$set": {"present_count": {"$ifNull": [{"$arrayElemAt": ["$daily.present_count", 0]}, 0]}, "late_count": {"$ifNull": [{"$arrayElemAt": ["$daily.late_count", 0]}, 0]}}},
      {"$lookup": {"from": "employees", "let": {"d": "$date"}, "pipeline": [{"$match": {"department": department, "$expr": {"$lte": ["$joined_on", "$$d"]}}}, {"$count": "n"}], "as": "hc"}},
      {"$set": {"headcount": {"$ifNull": [{"$arrayElemAt": ["$hc.n", 0]}, 0]} }},
      {"$set": {"attendance_rate": {"$cond": [{"$and": ["$is_working_day", {"$gt": ["$headcount", 0]}]}, {"$divide": ["$present_count", "$headcount"]}, None]}}},
      {"$setWindowFields": {"sortBy": {"_id": 1}, "output": {"moving_avg_7d": {"$avg": "$attendance_rate", "window": {"documents": [-6, 0]}}}}},
      {"$project": {"_id": 0, "date": 1, "is_working_day": 1, "headcount": 1, "present_count": 1, "late_count": 1, "attendance_rate": 1, "moving_avg_7d": 1}}, {"$sort": {"date": 1}}]


@app.get("/analytics/departments/{department}/trend")
def department_trend(department: str, from_date: str = Query(..., alias="from"), to_date: str = Query(..., alias="to")):
    valid_date(from_date); valid_date(to_date)
    first, last = date.fromisoformat(from_date), date.fromisoformat(to_date)
    if last < first or (last-first).days+1 > 92: raise HTTPException(422, "invalid date range; maximum is 92 days")
    if not db.employees.find_one({"department": department}, {"_id": 1}): raise HTTPException(404, "department not found")
    rows = list(db.attendance_logs.aggregate(trend_pipeline(department, from_date, to_date), allowDiskUse=True))
    # Decimal half-up is applied to the reported rates to avoid binary/banker's rounding.
    for r in rows:
        for key in ("attendance_rate", "moving_avg_7d"):
            if r[key] is not None: r[key] = rounded(float(r[key]), 4)
    return {"department": department, "items": rows}


def serialize_explain(value):
    return json.loads(json_util.dumps(value))


@app.get("/admin/explain/{endpoint}")
def explain(endpoint: str, emp_code: str | None = None, month: str | None = None, department: str | None = None,
            limit: int = Query(10, ge=1, le=50), date_from: str | None = None, date_to: str | None = None,
            status: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
            from_date: str | None = Query(None, alias="from"), to_date: str | None = Query(None, alias="to")):
    if endpoint == "attendance_list":
        q = attendance_filter(emp_code, date_from, date_to, status)
        exp = db.command("explain", {"find": "attendance_logs", "filter": q, "sort": {"date": -1, "emp_code": 1}, "skip": (page-1)*page_size, "limit": page_size}, verbosity="executionStats")
        collection = "attendance_logs"
    elif endpoint == "employee_monthly":
        if not emp_code or not month: raise HTTPException(422, "emp_code and month are required")
        exp = db.command("explain", {"aggregate": "attendance_logs", "pipeline": employee_month_pipeline(emp_code, month), "cursor": {}}, verbosity="executionStats"); collection = "attendance_logs"
    elif endpoint == "department_summary":
        if not month: raise HTTPException(422, "month is required")
        exp = db.command("explain", {"aggregate": "employees", "pipeline": dept_summary_pipeline(month, department), "cursor": {}}, verbosity="executionStats"); collection = "employees"
    elif endpoint == "late_leaderboard":
        if not month: raise HTTPException(422, "month is required")
        exp = db.command("explain", {"aggregate": "attendance_logs", "pipeline": leaderboard_pipeline(month, department, limit), "cursor": {}}, verbosity="executionStats"); collection = "attendance_logs"
    elif endpoint == "department_trend":
        if not department or not from_date or not to_date: raise HTTPException(422, "department, from and to are required")
        valid_date(from_date); valid_date(to_date)
        first, last = date.fromisoformat(from_date), date.fromisoformat(to_date)
        if last < first or (last-first).days+1 > 92: raise HTTPException(422, "invalid date range; maximum is 92 days")
        exp = db.command("explain", {"aggregate": "employees", "pipeline": trend_pipeline(department, from_date, to_date), "cursor": {}}, verbosity="executionStats"); collection = "employees"
    else: raise HTTPException(422, "unknown endpoint")
    return {"endpoint": endpoint, "collection": collection, "explain": serialize_explain(exp)}
