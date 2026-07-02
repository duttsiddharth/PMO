# Delivery Board integration (from SD Delivery OS prototype)

## What's added
1. **Delivery Board module** (`modules/delivery_board.py`) — new page:
   - Portfolio view: every project as a card with RAG dot + delivery rail
     (Presales → Planning → Execution → Closure).
   - Project view: clickable stage/RAG controls (permission-gated), blocked-task
     alert, and a kanban board (Not Started / In Progress / Blocked / Complete)
     with one-click Advance.
2. **Two new roles** — Sponsor (read + financials) and Vendor (moves only
   their own tasks via an identity picker).
3. **Edit-level permissions** — `config.ROLE_PERMISSIONS` gates actions,
   complementing the existing `ROLE_VISIBILITY` which only gates pages.

## Files changed
- `modules/delivery_board.py`  (new)
- `config.py`                  (ROLES, STAGES, ROLE_VISIBILITY, ROLE_PERMISSIONS)
- `app.py`                     (import + NAV entry + role in session_state)
- `core/seed.py`               (all company, vendor, brand and client personal
                                names replaced with fictional/generic ones —
                                client is now 'Meridian Group')

## No migration needed
Rail stages map to the existing Project.status values; "Blocked" is just a
new string value for WBSTask.status. Existing SQLite/Supabase data is safe.

## Deploy
Drop the three files into `PMO/pm_toolkit/` (same paths), commit, push —
Streamlit Community Cloud redeploys automatically.
