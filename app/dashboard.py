"""Responsive browser dashboard served by the FastAPI application."""

INDEX_HTML = r"""<!doctype html>
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
</body></html>"""

FAVICON_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="18" fill="#63d1a5"/><path d="M18 15h8v14h12V15h8v34h-8V36H26v13h-8z" fill="#10293a"/></svg>'


NOT_FOUND_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="This page could not be found.">
  <title>Page not found | Attendance Hub</title>
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <style>
    body {
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 24px;
      background: #f5f8f7;
      color: #14243a;
      font: 16px/1.5 system-ui, sans-serif;
      text-align: center;
    }
    .box { max-width: 460px; }
    h1 { margin: 0; color: #176b58; font-size: clamp(2rem, 9vw, 4rem); }
    p { color: #64748b; }
    a {
      display: inline-block;
      margin-top: 12px;
      padding: 11px 18px;
      border-radius: 9px;
      background: #176b58;
      color: white;
      font-weight: 700;
      text-decoration: none;
    }
  </style>
</head>
<body>
  <main class="box">
    <h1>404</h1>
    <h2>Page not found</h2>
    <p>The link may be outdated, or the address may be incorrect.</p>
    <a href="/">Return to Attendance Hub</a>
  </main>
</body>
</html>"""
