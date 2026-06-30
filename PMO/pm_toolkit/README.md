# IT Infrastructure PM Toolkit

A production-shaped, Python + Streamlit project-management toolkit for running
IT infrastructure programmes — Telecom, WAN, LAN, SD-WAN, Network Refresh,
Firewall, Data Center / Cloud Migration, Unified Communications, Security and
Managed Services — across the full lifecycle from presales to closure.

Built under the **SD Advisory** brand.

---

## What's inside

A modular Streamlit app backed by a SQLAlchemy data model (SQLite by default,
PostgreSQL optional) with a real Earned Value Management engine, Plotly
visualisations, and PDF / Word / PowerPoint / Excel report generation.

### Modules (sidebar navigation)
| Module | Highlights |
|---|---|
| Executive Dashboard | Portfolio + single-project view, RAG health, full EVM KPIs (PV/EV/AC/SV/CV/SPI/CPI/EAC/ETC/VAC), burn-down, SPI×CPI scatter, AI summary |
| Project Initiation | Charter, business case, stakeholder register, RACI |
| Project Planning | WBS, dependencies, critical-path flag, Plotly Gantt, milestones |
| Resource Management | Directory, skills matrix, allocation/utilisation, capacity, timesheets |
| Budget & Financials | Planned vs actual, monthly spend, burn rate, forecast, EVM snapshot |
| RAID Management | Risks / Assumptions / Issues / Dependencies + 5×5 risk heat map |
| Change Management | CR register, cost/schedule impact, approval workflow |
| Vendor & Procurement | Vendor master, SLA, purchase orders, delivery/invoice tracking |
| Meeting Management | Agenda, MoM, decisions, action items |
| Migration Tracker | Per-site cutover status, rollback plans, acceptance |
| Quality Management | Audits, NCRs, corrective/preventive actions |
| PMO Compliance | Artifact checklist + compliance % (portfolio and project) |
| Customer Acceptance | Handover checklist, acceptance certificate preview |
| Lessons Learned | Successes, challenges, recommendations, best practices |
| Weekly Status Report | Auto-generated report → export to PDF/Word/PPTX/Excel |
| Reports & Exports | Full dataset export (Excel workbook, CSV) + summary PDF |

### Role-based access
Switch role in the sidebar (Admin / PM / Team Member / Customer). Visibility is
controlled in `config.ROLE_VISIBILITY`. Admin and PM see everything; Team Member
and Customer see a relevant subset.

---

## Quick start

```bash
cd pm_toolkit
python -m venv .venv && source .venv/bin/activate      # optional
pip install -r requirements.txt
python -m core.seed          # load 3 sample projects (optional but recommended)
streamlit run app.py
```

Then open the URL Streamlit prints (default http://localhost:8501).
You can also seed/reset data from the in-app **⚙ Settings** page.

---

## Configuration

All via environment variables (with sensible defaults):

| Variable | Default | Purpose |
|---|---|---|
| `PM_DATABASE_URL` | `sqlite:///data/pm_toolkit.db` | DB DSN; set a `postgresql+psycopg2://…` URL for Postgres |
| `PM_ORG_NAME` | `SD Advisory` | Branding in the sidebar |
| `ANTHROPIC_API_KEY` | _(unset)_ | If set, executive summaries are AI-generated; otherwise deterministic templates are used so the app always runs offline |
| `PM_AI_MODEL` | `claude-sonnet-4-6` | Model used when the API key is present |

---

## The EVM engine

`core/evm.py` computes the standard PMP metrics from WBS tasks:

```
PV  = Σ planned_cost
EV  = Σ planned_cost × %complete
AC  = Σ actual_cost
SV  = EV − PV     CV  = EV − AC
SPI = EV / PV     CPI = EV / AC
EAC = BAC / CPI   ETC = EAC − AC    VAC = BAC − EAC
```

**Design note (intentional simplification):** PV is the full planned value of
all scoped work (≈ BAC), so SPI behaves like a percent-complete index rather
than a time-phased schedule index. For a true time-phased SPI, add a planned
status-date baseline per task and compute PV as planned value *to date*. The
data model already carries task start/end dates to support that extension.

---

## Project structure

```
pm_toolkit/
├── app.py                  # Streamlit entry point + navigation + RBAC
├── config.py               # configuration (env-driven)
├── requirements.txt
├── README.md / INSTALL.md
├── .streamlit/config.toml  # theme
├── core/
│   ├── database.py         # engine / scoped session
│   ├── models.py           # SQLAlchemy ORM (full domain)
│   ├── evm.py              # Earned Value engine
│   ├── ai.py               # AI helpers (offline fallback)
│   └── seed.py             # sample data
├── modules/                # one render() per functional area
├── reporting/              # pdf / word / pptx / excel exporters
└── tests/                  # pytest suite (EVM + seed + report builders)
```

---

## Tests

```bash
pip install pytest
python -m pytest tests/ -q
```

Covers the EVM math (including divide-by-zero guards, over-budget/behind cases,
EAC), seeding + ORM relationships, and that all four report formats build.

---

## Notes & honest scope

This is a strong, runnable **foundation**, not a finished commercial product.
Implemented end-to-end: data layer, EVM, dashboards, charts, RAID, change,
budget, planning/Gantt, migration, quality, compliance, status report and all
four export formats, with sample data and tests.

Lighter / extension points you may want to build out for production:
- Persisted authentication (current RBAC is a role selector, not a login)
- Editable inline grids on every table (several use add-forms + read views)
- MS Project (.mpp/XML) import/export and email notifications (bonus items)
- AI risk/delay prediction is currently heuristic; wire `core/ai.py` to the
  Anthropic API (set `ANTHROPIC_API_KEY`) for model-generated narratives
- A newer Streamlit may warn that `use_container_width` is deprecated in favour
  of `width=`; the calls still function. Swap them if you pin a 2026+ release.

The modular layout means new modules slot in by adding a `render()` and one line
to the `NAV` registry in `app.py`.
