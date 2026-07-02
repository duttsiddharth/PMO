"""IT Infrastructure PM Toolkit — Streamlit application entry point.

Run:  streamlit run app.py
"""
import streamlit as st

import config
from core.database import init_db, Session
from core import models as m

_ICON = "📊"
try:  # use the brand mark as the page icon when available
    from PIL import Image
    _ICON = Image.open(config.BASE_DIR / "assets" / "icon.png")
except Exception:
    pass

# Module renderers
from modules import (
    dashboard, initiation, planning, resources, budget, raid, change, vendors,
    status_report, meetings, migration, pmo_compliance, reports, data_management,
    delivery_board,
)
from modules import quality as quality_mod

st.set_page_config(page_title=config.APP_NAME, page_icon=_ICON, layout="wide",
                   initial_sidebar_state="expanded")

init_db()


# Navigation registry: label -> (callable, icon)
NAV = {
    "Executive Dashboard": dashboard.render,
    "Delivery Board": delivery_board.render,
    "Project Initiation": initiation.render,
    "Project Planning": planning.render,
    "Resource Management": resources.render,
    "Budget & Financials": budget.render,
    "RAID Management": raid.render,
    "Change Management": change.render,
    "Vendor & Procurement": vendors.render,
    "Meeting Management": meetings.render,
    "Migration Tracker": migration.render,
    "Quality Management": quality_mod.render_quality,
    "PMO Compliance": pmo_compliance.render,
    "Customer Acceptance": quality_mod.render_acceptance,
    "Lessons Learned": quality_mod.render_lessons,
    "Weekly Status Report": status_report.render,
    "Reports & Exports": reports.render,
    "Data Management": data_management.render,
}


def _visible_sections(role: str):
    allowed = config.ROLE_VISIBILITY.get(role, "*")
    if allowed == "*":
        return list(NAV.keys())
    return [s for s in NAV if s in allowed]


def settings_page():
    st.markdown("### Settings")

    # --- Database status -------------------------------------------------
    backend = "PostgreSQL (persistent)" if config.IS_PERSISTENT_DB else "SQLite (ephemeral)"
    safe_url = config.DATABASE_URL
    if "@" in safe_url:  # hide credentials in any server DSN
        safe_url = safe_url.split("://", 1)[0] + "://***@" + safe_url.split("@", 1)[1]
    c1, c2 = st.columns(2)
    c1.metric("Database backend", backend.split(" (")[0])
    s = Session()
    try:
        n_proj = s.query(m.Project).count()
    except Exception:
        n_proj = 0
    c2.metric("Projects in database", n_proj)
    st.write(f"**Connection:** `{safe_url}`")

    if config.IS_PERSISTENT_DB:
        st.success("Backed by a persistent server database — data survives reboots.")
    else:
        st.warning("Using ephemeral SQLite. Data resets when the app reboots or "
                   "redeploys. Set `PM_DATABASE_URL` (e.g. Supabase) for persistence "
                   "— see the expander below.")

    if st.button("🔌 Test database connection"):
        try:
            from sqlalchemy import text
            from core.database import engine
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            st.success("Connection OK.")
        except Exception as exc:
            st.error(f"Connection failed: {exc}")

    with st.expander("How to switch to Supabase / PostgreSQL (persistent)"):
        st.markdown(
            "1. In Supabase: **Project Settings → Database → Connection string → "
            "URI** (use the **Session pooler**, port 5432).\n"
            "2. In this app on Streamlit Cloud: **Manage app → Settings → Secrets**, add:\n"
        )
        st.code('PM_DATABASE_URL = "postgresql://postgres.[ref]:[PASSWORD]@'
                'aws-0-[region].pooler.supabase.com:5432/postgres"', language="toml")
        st.markdown(
            "3. Save — the app reboots. No code change needed; `postgres://` and "
            "`postgresql://` are both accepted.\n"
            "4. Come back here and click **Seed / reset sample data** once to create "
            "the tables, or just start adding real data in **Data Management**."
        )

    st.divider()
    # --- Seed ------------------------------------------------------------
    st.warning("Seeding resets ALL data and loads 3 sample projects.")
    if st.button("Seed / reset sample data"):
        from core.seed import seed
        seed()
        st.success("Sample data loaded. Navigate to the Executive Dashboard.")
        st.rerun()


def main():
    _logo = config.BASE_DIR / "assets" / "logo.png"
    if _logo.exists():
        try:
            st.logo(str(_logo), icon_image=str(_logo), size="large")
        except Exception:
            pass
        lc = st.sidebar.columns([1, 2, 1])
        lc[1].image(str(_logo), width=92)
    st.sidebar.markdown(
        f"<div style='text-align:center;font-weight:800;font-size:1.25rem;"
        f"margin:.1rem 0 0'>{config.ORG_NAME}</div>"
        f"<div style='text-align:center;color:#94A3B8;font-size:.8rem;"
        f"margin-bottom:.4rem'>{config.APP_NAME}</div>",
        unsafe_allow_html=True,
    )

    role = st.sidebar.selectbox("Role", config.ROLES, index=1)  # default PM
    st.session_state["role"] = role
    theme = st.sidebar.radio("Theme", ["Dark", "Light"], horizontal=True)
    from modules import theme as _theme
    _theme.inject_css(dark=(theme == "Dark"))

    sections = _visible_sections(role)
    st.sidebar.divider()
    choice = st.sidebar.radio("Navigate", sections + ["⚙ Settings"], label_visibility="collapsed")

    st.sidebar.divider()
    st.sidebar.caption(f"Signed in as **{role}**")
    st.sidebar.caption("© SD Advisory · sample toolkit")

    if choice == "⚙ Settings":
        settings_page()
    else:
        try:
            NAV[choice]()
        except Exception as exc:  # keep the app alive; surface the error
            st.error(f"Error rendering '{choice}': {exc}")
            if st.session_state.get("debug"):
                st.exception(exc)
    # Return this run's scoped session to the pool so connections never leak.
    Session.remove()


if __name__ == "__main__":
    main()
