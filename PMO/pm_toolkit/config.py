"""Central configuration for the PM Toolkit.

Reads from environment variables where present so the same code base can run
on SQLite (default, zero-config) or PostgreSQL in production.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# --- Database -------------------------------------------------------------
# Default: local SQLite file. Set PM_DATABASE_URL to a PostgreSQL DSN to
# switch, e.g. postgresql+psycopg2://user:pass@host:5432/pmtoolkit
DATABASE_URL = os.getenv(
    "PM_DATABASE_URL",
    f"sqlite:///{DATA_DIR / 'pm_toolkit.db'}",
)

# --- Branding -------------------------------------------------------------
APP_NAME = "IT Infrastructure PM Toolkit"
ORG_NAME = os.getenv("PM_ORG_NAME", "SD Advisory")
THEME_PRIMARY = "#2563EB"

# --- Roles ----------------------------------------------------------------
ROLES = ["Admin", "PM", "Team Member", "Customer"]

# Which navigation sections each role may open. Admin/PM see everything.
ROLE_VISIBILITY = {
    "Admin": "*",
    "PM": "*",
    "Team Member": [
        "Executive Dashboard", "Project Planning", "Resource Management",
        "RAID Management", "Meeting Management", "Migration Tracker",
        "Quality Management", "Weekly Status Report",
    ],
    "Customer": [
        "Executive Dashboard", "Customer Acceptance", "Weekly Status Report",
        "PMO Compliance",
    ],
}

# --- AI (optional) --------------------------------------------------------
# If set, the AI helpers in core/ai.py call the Anthropic API. If unset, the
# toolkit falls back to deterministic template-based summaries so it always
# runs offline.
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
AI_MODEL = os.getenv("PM_AI_MODEL", "claude-sonnet-4-6")

PROJECT_TYPES = [
    "Telecom", "WAN", "LAN", "SD-WAN", "Network Refresh", "Firewall",
    "Data Center Migration", "Cloud Migration", "Unified Communications",
    "Security", "Managed Services",
]
