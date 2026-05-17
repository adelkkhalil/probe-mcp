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
