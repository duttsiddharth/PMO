"""Resource Management: directory, skills matrix, allocation, capacity, timesheets."""
import pandas as pd
import plotly.express as px
import streamlit as st

from core import models as m
from modules.common import get_session, section_title


def render():
    section_title("Resource Management", "Team directory, skills, allocation and utilisation")
    s = get_session()
    resources = s.query(m.Resource).all()

    tab_dir, tab_alloc, tab_time = st.tabs(["Directory & Skills", "Allocation & Capacity", "Timesheets"])

    with tab_dir:
        df = pd.DataFrame([{ "Name": r.name, "Role": r.role, "Skills": r.skills,
                             "Cost/hr": r.cost_rate, "Capacity (h/wk)": r.capacity_hours}
                           for r in resources])
        st.dataframe(df, use_container_width=True, hide_index=True)
        # Skills matrix (resource x skill presence)
        all_skills = sorted({sk.strip() for r in resources for sk in (r.skills or "").split(",") if sk.strip()})
        matrix = []
        for r in resources:
            owned = {sk.strip() for sk in (r.skills or "").split(",")}
            matrix.append({"Resource": r.name, **{sk: ("✓" if sk in owned else "") for sk in all_skills}})
        if matrix:
            st.markdown("**Skills Matrix**")
            st.dataframe(pd.DataFrame(matrix), use_container_width=True, hide_index=True)

    with tab_alloc:
        allocs = s.query(m.Allocation).all()
        rows = []
        for a in allocs:
            rows.append({"Resource": a.resource.name, "Project": a.project.code,
                         "Allocation %": a.allocation_pct})
        adf = pd.DataFrame(rows)
        if not adf.empty:
            util = adf.groupby("Resource")["Allocation %"].sum().reset_index()
            util["Status"] = util["Allocation %"].apply(
                lambda x: "Over-allocated" if x > 100 else ("Full" if x == 100 else "Available"))
            fig = px.bar(util, x="Resource", y="Allocation %", color="Status",
                         color_discrete_map={"Over-allocated": "#DC2626", "Full": "#F59E0B",
                                             "Available": "#16A34A"}, title="Resource Utilisation")
            fig.add_hline(y=100, line_dash="dash", line_color="grey")
            fig.update_layout(height=360, margin=dict(t=40))
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(adf, use_container_width=True, hide_index=True)
        else:
            st.info("No allocations yet.")

    with tab_time:
        ts = s.query(m.Timesheet).all()
        rows = [{ "Resource": t.resource.name, "Project": t.project.code,
                  "Week ending": t.week_ending, "Planned h": round(t.planned_hours, 1),
                  "Actual h": round(t.actual_hours, 1),
                  "Variance h": round(t.actual_hours - t.planned_hours, 1)} for t in ts]
        tdf = pd.DataFrame(rows)
        if not tdf.empty:
            agg = tdf.groupby("Week ending")[["Planned h", "Actual h"]].sum().reset_index()
            fig = px.line(agg, x="Week ending", y=["Planned h", "Actual h"], markers=True,
                          title="Planned vs Actual Hours")
            fig.update_layout(height=320, margin=dict(t=40))
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(tdf, use_container_width=True, hide_index=True)
        else:
            st.info("No timesheet data yet.")
