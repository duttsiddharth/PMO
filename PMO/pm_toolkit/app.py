"""IT Infrastructure PM Toolkit — Streamlit application entry point.

Run:  streamlit run app.py
"""
import streamlit as st

import config
from core.database import init_db, Session
from core import models as m

# Module renderers
from modules import (
    dashboard, initiation, planning, resources, budget, raid, change, vendors,
    status_report, meetings, migration, pmo_compliance, reports,
)
from modules import quality as quality_mod

st.set_page_config(page_title=config.APP_NAME, page_icon="📊", layout="wide",
                   initial_sidebar_state="expanded")

init_db()


# Navigation registry: label -> (callable, icon)
NAV = {
    "Executive Dashboard": dashboard.render,
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
}


def _visible_sections(role: str):
    allowed = config.ROLE_VISIBILITY.get(role, "*")
    if allowed == "*":
        return list(NAV.keys())
    return [s for s in NAV if s in allowed]


def settings_page():
    st.markdown("### Settings")
    st.write(f"**Database:** `{config.DATABASE_URL}`")
    st.write(f"**AI mode:** {'Anthropic API' if config.ANTHROPIC_API_KEY else 'Offline templates'}")
    s = Session()
    n_proj = s.query(m.Project).count()
    st.write(f"**Projects in database:** {n_proj}")
    st.divider()
    st.warning("Seeding resets all data and loads 3 sample projects.")
    if st.button("Seed / reset sample data"):
        from core.seed import seed
        seed()
        st.success("Sample data loaded. Navigate to the Executive Dashboard.")
        st.rerun()


def main():
    st.sidebar.markdown(f"## 📊 {config.ORG_NAME}")
    st.sidebar.caption(config.APP_NAME)

    role = st.sidebar.selectbox("Role", config.ROLES, index=1)  # default PM
    theme = st.sidebar.radio("Theme", ["Light", "Dark"], horizontal=True)
    if theme == "Dark":
        st.markdown("<style>.stApp{background:#0F172A;color:#E2E8F0}</style>", unsafe_allow_html=True)

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


if __name__ == "__main__":
    main()
