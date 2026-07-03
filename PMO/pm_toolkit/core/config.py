"""Central configuration for the PM Toolkit.

Reads from environment variables where present so the same code base can run
on SQLite (default, zero-config) or PostgreSQL in production.
"""
import os
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _setting(name: str, default: str = "") -> str:
    """Read a setting from environment first, then Streamlit secrets.

    On Streamlit Community Cloud, values pasted into the Secrets box are exposed
    as environment variables, but reading st.secrets as a fallback makes the
    same code work whether secrets arrive as env vars or a secrets.toml.
    """
    val = os.getenv(name)
    if val:
        return val
    try:
        import streamlit as st  # optional; absent in pure-CLI contexts
        if hasattr(st, "secrets") and name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    return default


def _normalize_db_url(url: str) -> str:
    """Make common Postgres/Supabase DSNs work with SQLAlchemy 2.0 + psycopg2.

    Supabase and many providers hand out 'postgres://...' or 'postgresql://...'.
    SQLAlchemy 2.0 needs an explicit driver, so we route both to psycopg2.
    """
    if url.startswith("postgres://"):
        url = "postgresql+psycopg2://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url


def _writable_data_dir() -> Path:
    """Return a directory we can actually write the SQLite file into.

    On platforms like Streamlit Community Cloud the cloned repo tree
    (/mount/src/...) is read-only, so creating the .db file inside the project
    fails with 'unable to open database file'. We try the project ./data dir
    first; if it isn't writable we fall back to a temp directory.
    """
    candidate = BASE_DIR / "data"
    try:
        candidate.mkdir(parents=True, exist_ok=True)
        probe = candidate / ".write_test"
        probe.touch()
        probe.unlink()
        return candidate
    except OSError:
        fallback = Path(tempfile.gettempdir()) / "pm_toolkit_data"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


DATA_DIR = _writable_data_dir()

# --- Database -------------------------------------------------------------
# Default: local SQLite file (in a writable dir). Set PM_DATABASE_URL to a
# PostgreSQL DSN to switch, e.g.
#   postgresql+psycopg2://user:pass@host:5432/pmtoolkit
# A persistent Postgres/Supabase URL is recommended for cloud hosting, since
# the SQLite fallback lives in ephemeral storage and resets on reboot.
_raw_db_url = _setting("PM_DATABASE_URL", f"sqlite:///{DATA_DIR / 'pm_toolkit.db'}")
DATABASE_URL = _normalize_db_url(_raw_db_url)

# True when backed by a persistent server DB (not ephemeral SQLite).
IS_PERSISTENT_DB = not DATABASE_URL.startswith("sqlite")

# --- Branding -------------------------------------------------------------
APP_NAME = "IT Infrastructure PM Toolkit"
ORG_NAME = _setting("PM_ORG_NAME", "SD Advisory")
THEME_PRIMARY = "#2563EB"

# --- Roles ----------------------------------------------------------------
ROLES = ["Admin", "PM", "Sponsor", "Team Member", "Vendor", "Customer"]

# Delivery lifecycle stages shown on the Delivery Board rail. These map 1:1
# to the existing Project.status values, so no data migration is required.
STAGES = ["Presales", "Planning", "Execution", "Closure"]

# Which navigation sections each role may open. Admin/PM see everything.
ROLE_VISIBILITY = {
    "Admin": "*",
    "PM": "*",
    "Sponsor": [
        "Executive Dashboard", "Portfolio Weekly Digest", "Delivery Board", "Budget & Financials",
        "RAID Management", "Change Management", "Weekly Status Report",
        "PMO Compliance", "Reports & Exports",
    ],
    "Team Member": [
        "Executive Dashboard", "Delivery Board", "Project Planning",
        "Resource Management", "RAID Management", "Meeting Management",
        "Migration Tracker", "Quality Management", "Weekly Status Report",
    ],
    "Vendor": [
        "Delivery Board", "Vendor & Procurement", "Migration Tracker",
        "Weekly Status Report",
    ],
    "Customer": [
        "Executive Dashboard", "Portfolio Weekly Digest", "Delivery Board", "Customer Acceptance",
        "Weekly Status Report", "PMO Compliance",
    ],
}

# Edit-level permissions consumed by modules/delivery_board.py (page
# visibility above controls what you can SEE; this controls what you can DO).
#   edit_tasks     – move/advance any task on the kanban board
#   edit_own_tasks – move only tasks whose owner matches the chosen identity
#   edit_stage     – advance the project lifecycle stage
#   edit_rag       – change the project health (RAG)
#   view_finance   – see budget / actuals on the delivery board
ROLE_PERMISSIONS = {
    "Admin": ["edit_tasks", "edit_stage", "edit_rag", "view_finance"],
    "PM": ["edit_tasks", "edit_stage", "edit_rag", "view_finance"],
    "Sponsor": ["view_finance"],
    "Team Member": ["edit_tasks"],
    "Vendor": ["edit_own_tasks"],
    "Customer": [],
}

# --- Role protection (optional) --------------------------------------------
# Set PM_ROLE_PINS (env var or Streamlit secret) to require a PIN for chosen
# roles, e.g.  PM_ROLE_PINS = "Admin:2468,PM:1357"
# When unset (default) every role is freely selectable — identical to the
# original behaviour, so demos keep working with zero configuration.
def _parse_role_pins(raw: str) -> dict:
    pins = {}
    for part in raw.split(","):
        if ":" in part:
            role, pin = part.split(":", 1)
            role, pin = role.strip(), pin.strip()
            if role and pin:
                pins[role] = pin
    return pins


ROLE_PINS = _parse_role_pins(_setting("PM_ROLE_PINS", ""))

# --- AI (optional) --------------------------------------------------------
# If set, the AI helpers in core/ai.py call the Anthropic API. If unset, the
# toolkit falls back to deterministic template-based summaries so it always
# runs offline.
ANTHROPIC_API_KEY = _setting("ANTHROPIC_API_KEY", "")
AI_MODEL = _setting("PM_AI_MODEL", "claude-sonnet-4-6")

PROJECT_TYPES = [
    "Telecom", "WAN", "LAN", "SD-WAN", "Network Refresh", "Firewall",
    "Data Center Migration", "Cloud Migration", "Unified Communications",
    "Security", "Managed Services",
]
