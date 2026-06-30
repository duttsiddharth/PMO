# Installation Guide

## Prerequisites
- Python 3.12+ (3.10+ works)
- pip

## 1. Install
```bash
cd pm_toolkit
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Load sample data (recommended)
```bash
python -m core.seed
```
Creates `data/pm_toolkit.db` with 3 fully-populated sample projects.
You can also do this later from the in-app **⚙ Settings** page.

## 3. Run
```bash
streamlit run app.py
```
Open the printed URL (default http://localhost:8501).

## 4. (Optional) PostgreSQL instead of SQLite
```bash
pip install psycopg2-binary
export PM_DATABASE_URL="postgresql+psycopg2://user:pass@localhost:5432/pmtoolkit"
python -m core.seed
streamlit run app.py
```

## 5. (Optional) Enable AI summaries
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
# optionally: export PM_AI_MODEL="claude-sonnet-4-6"
pip install anthropic
```
Without a key, the toolkit uses deterministic template summaries and runs fully
offline.

## 6. Run tests
```bash
pip install pytest
python -m pytest tests/ -q
```

## Troubleshooting
- **Blank page / "No projects yet":** run `python -m core.seed` or use the
  Settings page to seed data.
- **Port in use:** `streamlit run app.py --server.port 8502`.
- **Reset everything:** delete `data/pm_toolkit.db` (or re-seed; seeding resets).
