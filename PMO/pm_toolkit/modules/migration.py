"""Migration Tracker: WAN/LAN/DC/Cloud/Firewall/SD-WAN site cutover tracking."""
import pandas as pd
import plotly.express as px
import streamlit as st
from modules.theme import style_fig

from core import models as m
from modules.common import project_picker, get_session, section_title
from core.crud import editable_grid

MIG_TYPES = ["WAN", "LAN", "Data Center", "Cloud", "Firewall", "SD-WAN"]
STATUSES = ["Planned", "In Progress", "Migrated", "Rolled Back"]


def render():
    section_title("Migration Tracker", "Site-level cutover status, rollback plans and acceptance")
    p = project_picker(key="mig_proj")
    s = get_session()

    with st.expander("✏️ Edit migration sites (inline grid: add / edit / delete)"):
        editable_grid(m.MigrationSite, scope_fk="project_id", scope_id=p.id, key=f"mig_grid_{p.id}")

    sites = p.migrations
    df = pd.DataFrame([{ "Type": x.migration_type, "Site": x.site, "Scheduled": x.scheduled_date,
                         "Status": x.status, "Acceptance": x.acceptance,
                         "Rollback Plan": x.rollback_plan} for x in sites])
    if not df.empty:
        k = st.columns(4)
        k[0].metric("Sites", len(df))
        k[1].metric("Migrated", int((df["Status"] == "Migrated").sum()))
        k[2].metric("In Progress", int((df["Status"] == "In Progress").sum()))
        k[3].metric("Accepted", int((df["Acceptance"] == "Accepted").sum()))

        counts = df["Status"].value_counts().reindex(STATUSES).fillna(0).reset_index()
        counts.columns = ["Status", "Count"]
        fig = px.bar(counts, x="Status", y="Count", color="Status",
                     color_discrete_map={"Planned": "#94A3B8", "In Progress": "#F59E0B",
                                         "Migrated": "#16A34A", "Rolled Back": "#DC2626"},
                     title="Migration Progress")
        fig.update_layout(height=320, margin=dict(t=40), showlegend=False)
        st.plotly_chart(style_fig(fig), width='stretch', config={"displayModeBar": False})
    st.dataframe(df, width='stretch', hide_index=True)

    with st.expander("Add migration site"):
        with st.form("add_site"):
            c = st.columns(3)
            mtype = c[0].selectbox("Type", MIG_TYPES)
            site = c[1].text_input("Site")
            sched = c[2].date_input("Scheduled date")
            status = c[0].selectbox("Status", STATUSES)
            acceptance = c[1].selectbox("Acceptance", ["Pending", "Accepted"])
            rollback = st.text_area("Rollback plan")
            if st.form_submit_button("Add") and site:
                s.add(m.MigrationSite(project_id=p.id, migration_type=mtype, site=site,
                                      scheduled_date=sched, status=status, acceptance=acceptance,
                                      rollback_plan=rollback))
                s.commit(); st.rerun()
