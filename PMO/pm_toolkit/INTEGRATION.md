# PMO Toolkit — Integration Pack v2

Drop these files into `PMO/pm_toolkit/` at the same paths, commit and push.
Streamlit Community Cloud redeploys automatically. No database migration is
required by any change in this pack.

## 1. Delivery Board (new page)
- `modules/delivery_board.py` (new) — portfolio delivery rail + kanban task
  board with role-aware editing.

## 2. Roles & permissions
- `config.py` — adds Sponsor and Vendor roles, STAGES, ROLE_PERMISSIONS
  (action-level gating on top of the existing page-level ROLE_VISIBILITY).

## 3. Sanitized sample data
- `core/seed.py` — all company, vendor, brand and client personal names
  replaced with fictional/generic ones (client is now "Meridian Group").
  After deploying, run Seed/reset from Settings once (this wipes data —
  export anything real first).

## 4. MACD on applicable pages (v2)
- `modules/common.py` — new `macd_panel()` helper: role-gated (Admin/PM)
  inline add/change/delete grid, reusing the existing core/crud engine.
- `modules/planning.py` — MACD for WBS tasks and Milestones.
- `modules/meetings.py` — MACD for Meetings.
- `modules/initiation.py` — MACD for Stakeholders.
- `modules/pmo_compliance.py` — MACD for Compliance artifacts.
  (Budget, RAID, Change, Vendors, Resources, Migration and Quality already
  had inline grids; Data Management remains the central console.)

## 5. Knowledge Intake / KB (new page, v2)
- `modules/kb_intake.py` (new) — upload an RFP / SOW / Solution Design /
  Charter (PDF, DOCX, TXT, MD); the toolkit extracts charter fields,
  milestones and risks, lets you review/edit, then applies them to a new or
  existing project ("fill empty only" by default, optional overwrite).
- `core/ai.py` — new `extract_project_fields()`: AI extraction when
  ANTHROPIC_API_KEY is set; deterministic heading-based parser otherwise,
  so the page works fully offline.
- `requirements.txt` — adds `pypdf` for PDF text extraction.
- Note: scanned/image-only PDFs need OCR first; the page will tell you.

## 6. App shell
- `app.py` — registers "Delivery Board" and "Knowledge Intake (KB)" in the
  left-side navigation and stores the selected role in session state.
