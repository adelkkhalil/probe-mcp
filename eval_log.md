# probe_mcp — Manual Eval Log

## Setup
- Database: Northwind SQLite
- MCP Server: northwind-raw (raw, no semantic layer)
- Client: Claude Desktop (Haiku 4.5)
- Date: 2026-05-18

---

## Task 01 — Find customers by country
**Prompt:** "Find me all customers from Germany"
**Tools called:** get_customers(country="Germany")
**Result:** PASS
**Observations:**
- Correctly passed country as a parameter
- Returned 11 customers, formatted cleanly
- 1 tool call, efficient

---

## Task 02 — Filter orders by natural language shipper name
**Prompt:** "Find me orders for customer ALFKI shipped via express courier"
**Tools called:** get_orders(customer_id="ALFKI") — no shipper filter
**Result:** PARTIAL FAIL
**Observations:**
- Never called get_shippers to look up shipper codes
- Used training knowledge to guess ShipVia meanings (got lucky — Northwind is well known)
- In a real system with unknown shippers this would return wrong results silently
- Fetched 126 orders and filtered in memory instead of passing ship_via to the query
- Root cause: ShipVia is an opaque integer with no description, shippers not referenced in tool description

---

## Task 03 — Identify overdue orders
**Prompt:** "Which orders are overdue — meaning the required date has passed but they haven't shipped yet?"
**Tools called:** zero — reused previous context
**Result:** PARTIAL FAIL
**Observations:**
- Correctly understood NULL ShippedDate = not yet shipped
- Correctly compared RequiredDate to today
- But silently scoped answer to ALFKI only (leftover from previous query)
- Made no new tool calls for a fresh question
- Note: stale context is partly a chat UI issue, not purely an MCP issue

---

## Task 04 — Top performing employee by order count
**Prompt:** "Who is our top performing employee by number of orders handled?"
**Tools called:** get_employees(), get_orders() — then failed
**Result:** FAIL
**Observations:**
- get_orders with no filter hit the 1MB tool result size limit
- No aggregate tool exists — agent had to fetch everything and process in memory
- Agent gave up and suggested useless fallbacks (upload CSV, use Salesforce)
- Root cause 1: missing get_top_employees or get_order_summary aggregate tool
- Root cause 2: get_orders has no limit parameter, returns unbounded results
- Root cause 3: no error guidance in tool description for large result sets

---

## Failure Pattern Summary

| # | Pattern | Tasks affected |
|---|---------|---------------|
| 1 | Agent uses training knowledge instead of available lookup tool | 02 |
| 2 | Fetches all rows, filters in memory instead of at DB level | 02, 04 |
| 3 | No aggregate tools — count, sum, rank impossible without blowing limits | 04 |
| 4 | No row limit on tools — unbounded queries hit size ceiling | 04 |
| 5 | Opaque integer fields with no enum description | 02 |

---

## Next Steps
- Add limit parameter to get_orders
- Add get_order_summary aggregate tool
- Add shipper enum to get_orders description
- Build semantic version of server and re-run same tasks
- Compare pass rates between raw and semantic server

---

## Semantic Server Results
- MCP Server: northwind-semantic (semantic layer)
- Same 4 tasks re-run for comparison

---

## Task 01S — Find customers by country (semantic)
**Prompt:** "Find me all customers from Germany"
**Tools called:** customers_by_country(country="Germany")
**Result:** PASS
**Observations:**
- Identical result to raw server, correct and efficient
- 1 tool call

---

## Task 02S — Filter orders by natural language shipper name (semantic)
**Prompt:** "Find me orders for customer ALFKI shipped via express courier"
**Tools called:** shippers(), then orders(customer_id="ALFKI", ship_via=1)
**Result:** PASS
**Observations:**
- Called shippers() first — used actual data, not training knowledge
- Correctly identified ShipVia=1 (Speedy Express) from the lookup
- Passed ship_via filter to orders() — database did the filtering
- Did not fetch 126 rows into memory
- Freight displayed as USD — agent understood currency from description
- Ambiguity note: "express courier" could mean Speedy Express or
  United Package — agent made a reasonable judgment call
- Comparison: RAW = fetched 126 rows, guessed shipper from training
  knowledge. SEMANTIC = 2 targeted tool calls, correct filter applied.

---

## Task 03S — Identify overdue orders (semantic)
**Prompt:** "Which orders are overdue — meaning the required date has passed but they haven't shipped yet?"
**Tools called:** orders() — default limit 50
**Result:** PARTIAL PASS
**Observations:**
- 1 tool call, correct tool selected
- Correctly understood NULL ShippedDate = not yet shipped (docstring worked)
- Correctly found zero genuinely overdue orders in the sample
- Proactively pivoted to find orders shipped after required date —
  good agent judgment, added value beyond the literal question
- Found 4 late shipments: Orders 10271, 10302, 10320 (1 day late each)
  and Order 10427 / PICCO (7 days late, flagged as most problematic)
- Problem: only checked 50 rows, stated conclusions without flagging
  it was working from an incomplete sample
- Agent showed no awareness of the limit — presented findings as if
  they covered the full database
- Root cause: default limit of 50 is too small for analytical queries,
  and the docstring does not warn the agent about this
- Fix needed: add note to orders() docstring that analytical queries
  should use limit=200 or paginate across the full dataset
- Comparison: RAW = answered from stale ALFKI context only.
  SEMANTIC = checked actual data, correct logic, good judgment,
  but silent sampling problem.

---

## Task 04S — Top performing employee by order count (semantic)
**Prompt:** "Who is our top performing employee by number of orders handled?"
**Tools called:** employees(), orders(limit=50), then in-memory grouping
**Result:** PARTIAL PASS
**Observations:**
- Did not crash — limit parameter prevented 1MB failure
- Got a result vs complete failure on raw server — clear improvement
- But: limit defaulted to 50, meaning order count is from incomplete data
  Employee 4 may have more than 37 orders total — answer is potentially wrong
- Returned Employee ID not name despite having called employees() already
  — did not join the data, ended with a question instead of a full answer
- Root cause 1: no aggregate tool — agent still doing grouping in memory
- Root cause 2: limit of 50 makes counts incorrect for large tables
- Root cause 3: tool descriptions do not guide agent to join employee
  names onto order results
- Comparison: RAW = complete failure, SEMANTIC = partial pass with
  correct structure but potentially wrong data

---

## Comparison Table

| Task | Raw Result | Semantic Result |
|------|-----------|-----------------|
| 01 — customers by country | PASS | PASS |
| 02 — orders by shipper name | PARTIAL FAIL | PASS |
| 03 — overdue orders | PARTIAL FAIL | PARTIAL PASS |
| 04 — top employee by orders | FAIL | PARTIAL PASS |
