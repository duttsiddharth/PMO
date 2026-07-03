"""Shared helpers used across Streamlit module pages."""
import pandas as pd
import streamlit as st

from core.database import Session
from core import models as m
from core.evm import compute_evm, EVMResult


# --------------------------------------------------------------------------
# Queries
# --------------------------------------------------------------------------
def get_session():
    return Session()


def list_projects():
    return get_session().query(m.Project).order_by(m.Project.code).all()


def get_project(pid):
    return get_session().query(m.Project).get(pid)


def project_evm(project) -> EVMResult:
    return compute_evm(project.tasks, project.budget)


def df(records, cols):
    """Build a DataFrame from ORM records given (label, attr) column specs."""
    rows = []
    for r in records:
        rows.append({label: getattr(r, attr, None) for label, attr in cols})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# UI helpers
# --------------------------------------------------------------------------
RAG_COLORS = {"Green": "#16A34A", "Amber": "#F59E0B", "Red": "#DC2626"}


def kpi(col, label, value, help_text=None, delta=None):
    col.metric(label, value, delta=delta, help=help_text)


def rag_badge(health: str) -> str:
    color = RAG_COLORS.get(health, "#64748B")
    return f"<span style='background:{color};color:white;padding:2px 10px;border-radius:12px;font-size:0.8rem'>{health}</span>"


def section_title(text: str, subtitle: str = ""):
    from modules.theme import header
    header(text, subtitle)


def macd_panel(model, *, scope_fk=None, scope_id=None, key, label):
    """Role-gated inline MACD (Move/Add/Change/Delete) grid for any entity.

    Renders the generic editable grid inside an expander. Only Admin and PM
    may modify records; other roles simply don't see the panel.
    """
    if st.session_state.get("role", "Customer") not in ("Admin", "PM"):
        return
    from core.crud import editable_grid
    with st.expander(f"🛠 MACD — {label} (add / change / delete records)"):
        editable_grid(model, scope_fk=scope_fk, scope_id=scope_id, key=key)


def project_picker(key="proj"):
    projects = list_projects()
    if not projects:
        st.warning("No projects yet. Seed sample data from the Settings page.")
        st.stop()
    labels = {f"{p.code} — {p.name}": p.id for p in projects}
    choice = st.selectbox("Project", list(labels.keys()), key=key)
    return get_project(labels[choice])
