# Starter code review

| # | Where | What is wrong | How you'd notice it | How it is fixed |
|---|---|---|---|---|
| 1 | `health` | Always returns ready without contacting MongoDB. | Stop MongoDB; endpoint still says `ok`. | Sends a ping and returns 503 on failure. |
| 2 | MongoClient setup | Indexes are never created, so natural-key races and large queries are not safe/fast. | Start against an unindexed database and inspect indexes. | Idempotent unique and query indexes are created at startup. |
| 3 | `EmployeeIn` | Required formats, lengths, dates and shift times are unchecked; equal shift endpoints are accepted. | Submit malformed code, date or `25:99`. | Pydantic validation enforces the API contract. |
| 4 | `create_employee` | Duplicate check then insert races; `created_at` is naive UTC/local ambiguous. | Send parallel creates for one `emp_code`. | Unique index is authoritative; duplicate-key maps to 409; timestamp is aware UTC. |
| 5 | `list_employees` | `skip` is one page too far, total ignores department, no sort, and falsey department is ignored. | Request page 1 or filter a department. | Filtered count, `(page-1)*page_size`, exact optional filter and ascending code sort. |
| 6 | `compute_late_minutes` | Naive timestamps and truncation can misread IST; shifts need the overnight attendance-day rule. | Test a 22:00 shift and a 05:30 punch. | UTC instants are converted to IST calendar dates and proper shift boundaries. |
| 7 | `compute_work_hours` | Python `round` uses ties-to-even, not half-up. | Use a duration exactly on a half-centesimal boundary. | Decimal `ROUND_HALF_UP` after whole-second truncation. |
| 8 | `compute_overtime` | End time is naive/incorrectly localized and always uses the same calendar day. | Punch out after midnight on an overnight shift. | Builds the shift end in IST on the following day when needed. |
| 9 | `punch_in` | Missing employee causes a 500; timestamp conversion uses host local time; falsy timestamp is treated as omitted; invalid status is accepted. | Use unknown code, epoch 0 or forbidden status. | 404 for unknown employee, strict epoch-millisecond validation, UTC conversion and presence-only status enum. |
| 10 | `punch_in` | Check-then-insert allows duplicate attendance under concurrency; returns Mongo `id`, which is not in the contract. | Parallel requests or inspect JSON keys. | Unique `(emp_code,date)` index and 409 mapping; response uses only contract fields. |
| 11 | `list_attendance` | Reads every matching document into Python, sorts and slices there; `_id` leaks as `id`. | Use a large collection / inspect response. | Count and indexed database sort/skip/limit; no internal identifier is exposed. |
| 12 | `list_attendance` | No date range validation, status validation or pagination bounds. | Reverse dates or request page size 1000. | Validated date/status values and page limits. |
| 13 | Endpoints and response conversion | Punch-out, correction and analytics are missing; BSON datetimes and legacy missing fields are not normalized. | Call any TODO route or inspect seeded legacy records. | Implemented routes and explicit epoch-ms serialization/defaults for history and computed values. |

Reviewed and retained: returning an empty `history` for a new punch is correct; punch events do not create audit entries. The employee business key is `emp_code`, not MongoDB `_id`.
