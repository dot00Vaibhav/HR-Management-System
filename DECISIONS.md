# Design decisions

1. Unique indexes on `employees.emp_code` and `(emp_code, date)` enforce identity and one daily record. Department/code, department/join-date, and join-date indexes support filters and headcount. Attendance date/code, date/code/status, and employee/punch-in indexes support lists, month scans and latest-punch lookup. I skipped a standalone status index because status has low selectivity.

2. Two punch-ins may both read the employee, then try the same attendance key. The unique index accepts one; the other raises `DuplicateKeyError`, mapped to 409. Correctness does not depend on check-then-insert.

3. `$rank` gives equal totals the same rank and skips the next rank. Filtering `rank <= limit` afterward returns every employee tied at the cutoff, ordered by total then employee code.

4. Department aggregation starts with employees joined by month end, then looks up logs. Employees with no matches survive the preserved unwind and count toward headcount; later joiners are excluded.

5. At 100x scale I would maintain daily facts or monthly summaries, then benchmark shard keys and query plans. Today summaries use indexed source collections.
