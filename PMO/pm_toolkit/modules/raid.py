"""RAID Management: Risks, Assumptions, Issues, Dependencies + Risk Heat Map."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core import models as m
from modules.common import project_picker, get_session, section_title

SEV_COLORS = {"Low": "#16A34A", "Medium": "#F59E0B", "High": "#F97316", "Critical": "#DC2626"}


def _raid_table(items, category):
    rows = []
    for r in items:
        if r.category != category:
            continue
        base = {"Title": r.title, "Owner": r.owner, "Severity": r.severity,
                "Status": r.status, "Due": r.due_date, "Mitigation": r.mitigation}
        if category == "Risk":
            base.update({"Prob": r.probability, "Impact": r.impact, "Score": r.risk_score})
        rows.append(base)
    return pd.DataFrame(rows)


def render():
    section_title("RAID Management", "Risks · Assumptions · Issues · Dependencies")
    p = project_picker(key="raid_proj")
    s = get_session()

    tabs = st.tabs(["Risks", "Assumptions", "Issues", "Dependencies", "Risk Heat Map"])
    cats = ["Risk", "Assumption", "Issue", "Dependency"]

    for tab, cat in zip(tabs[:4], cats):
        with tab:
            df = _raid_table(p.raid, cat)
            st.dataframe(df, use_container_width=True, hide_index=True)
            with st.expander(f"Add {cat}"):
                with st.form(f"add_{cat}"):
                    title = st.text_input("Title")
                    owner = st.text_input("Owner")
                    sev = st.selectbox("Severity", list(SEV_COLORS.keys()))
                    c = st.columns(2)
                    prob = c[0].slider("Probability (1-5)", 1, 5, 3) if cat == "Risk" else 3
                    impact = c[1].slider("Impact (1-5)", 1, 5, 3) if cat == "Risk" else 3
                    mitigation = st.text_area("Mitigation / Notes")
                    due = st.date_input("Due date")
                    if st.form_submit_button("Add") and title:
                        s.add(m.RaidItem(project_id=p.id, category=cat, title=title, owner=owner,
                                         severity=sev, probability=prob, impact=impact,
                                         mitigation=mitigation, due_date=due, status="Open"))
                        s.commit(); st.rerun()

    with tabs[4]:
        risks = [r for r in p.raid if r.category == "Risk"]
        if not risks:
            st.info("No risks logged.")
            return
        # Heat map grid 5x5 counting risks per (probability, impact)
        grid = [[0] * 5 for _ in range(5)]
        for r in risks:
            pr = max(1, min(5, r.probability or 1))
            im = max(1, min(5, r.impact or 1))
            grid[5 - pr][im - 1] += 1
        fig = go.Figure(data=go.Heatmap(
            z=grid, x=["1", "2", "3", "4", "5"], y=["5", "4", "3", "2", "1"],
            colorscale=[[0, "#DCFCE7"], [0.5, "#FEF08A"], [1, "#FCA5A5"]],
            text=grid, texttemplate="%{text}", showscale=True))
        fig.update_layout(title="Risk Heat Map (Probability × Impact)",
                          xaxis_title="Impact", yaxis_title="Probability", height=420)
        st.plotly_chart(fig, use_container_width=True)

        top = sorted(risks, key=lambda r: r.risk_score, reverse=True)[:5]
        st.markdown("**Top Risks by Exposure**")
        st.dataframe(pd.DataFrame([{ "Title": r.title, "Owner": r.owner, "Score": r.risk_score,
                                     "Severity": r.severity, "Status": r.status} for r in top]),
                     use_container_width=True, hide_index=True)
