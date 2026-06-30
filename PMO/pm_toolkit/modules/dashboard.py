"""Executive Dashboard: RAG health, EVM KPIs, burn-down, financial + resource charts."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core import models as m
from core.ai import executive_summary, predict_schedule_delay
from modules.common import (
    list_projects, project_picker, project_evm, get_session, section_title, RAG_COLORS,
)


def _portfolio_overview():
    projects = list_projects()
    rows = []
    for p in projects:
        e = project_evm(p)
        open_risks = sum(1 for r in p.raid if r.category == "Risk" and r.status == "Open")
        open_issues = sum(1 for r in p.raid if r.category == "Issue" and r.status == "Open")
        open_crs = sum(1 for c in p.changes if c.status in ("Submitted", "Under Review"))
        rows.append(dict(Project=p.code, Name=p.name, Customer=p.customer, Health=p.health,
                         Status=p.status, Complete=f"{e.percent_complete:.0f}%",
                         SPI=e.spi, CPI=e.cpi, AC=e.ac, BAC=e.bac,
                         Risks=open_risks, Issues=open_issues, CRs=open_crs))
    return pd.DataFrame(rows)


def render():
    section_title("Executive Dashboard", "Portfolio health and earned-value performance")

    tab_port, tab_proj = st.tabs(["Portfolio", "Single Project"])

    with tab_port:
        dfp = _portfolio_overview()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Projects", len(dfp))
        c2.metric("Open Risks", int(dfp["Risks"].sum()) if not dfp.empty else 0)
        c3.metric("Open Issues", int(dfp["Issues"].sum()) if not dfp.empty else 0)
        c4.metric("Open CRs", int(dfp["CRs"].sum()) if not dfp.empty else 0)

        if not dfp.empty:
            health_counts = dfp["Health"].value_counts().reindex(["Green", "Amber", "Red"]).fillna(0)
            fig = go.Figure(data=[go.Pie(
                labels=health_counts.index, values=health_counts.values, hole=0.55,
                marker=dict(colors=[RAG_COLORS[h] for h in health_counts.index]))])
            fig.update_layout(title="RAG Health Distribution", height=320, margin=dict(t=40, b=0))
            left, right = st.columns([1, 1.4])
            left.plotly_chart(fig, use_container_width=True)

            spi_cpi = px.scatter(dfp, x="SPI", y="CPI", text="Project", color="Health",
                                 color_discrete_map=RAG_COLORS, size="BAC", size_max=40,
                                 title="SPI vs CPI (target zone top-right)")
            spi_cpi.add_hline(y=1, line_dash="dash", line_color="grey")
            spi_cpi.add_vline(x=1, line_dash="dash", line_color="grey")
            spi_cpi.update_traces(textposition="top center")
            spi_cpi.update_layout(height=320, margin=dict(t=40, b=0))
            right.plotly_chart(spi_cpi, use_container_width=True)

            st.dataframe(dfp, use_container_width=True, hide_index=True)

    with tab_proj:
        p = project_picker(key="dash_proj")
        e = project_evm(p)

        head = st.columns([2, 1, 1, 1])
        head[0].markdown(f"#### {p.name}")
        head[1].markdown(f"**Health**")
        head[1].markdown(f"<span style='background:{RAG_COLORS.get(p.health)};color:#fff;"
                         f"padding:3px 12px;border-radius:12px'>{p.health}</span>", unsafe_allow_html=True)
        head[2].metric("Status", p.status)
        head[3].metric("Complete", f"{e.percent_complete:.0f}%")

        k = st.columns(4)
        k[0].metric("Earned Value (EV)", f"{e.ev:,.0f}")
        k[1].metric("Planned Value (PV)", f"{e.pv:,.0f}")
        k[2].metric("Actual Cost (AC)", f"{e.ac:,.0f}")
        k[3].metric("Budget (BAC)", f"{e.bac:,.0f}")

        k2 = st.columns(4)
        k2[0].metric("SPI", f"{e.spi:.2f}", delta=f"{(e.spi-1)*100:.0f}%")
        k2[1].metric("CPI", f"{e.cpi:.2f}", delta=f"{(e.cpi-1)*100:.0f}%")
        k2[2].metric("Schedule Var (SV)", f"{e.sv:,.0f}")
        k2[3].metric("Cost Var (CV)", f"{e.cv:,.0f}")

        k3 = st.columns(3)
        k3[0].metric("Estimate at Completion", f"{e.eac:,.0f}")
        k3[1].metric("Estimate to Complete", f"{e.etc:,.0f}")
        k3[2].metric("Variance at Completion", f"{e.vac:,.0f}")

        # Burn-down: remaining budget over phases (planned vs actual cumulative)
        tasks = sorted(p.tasks, key=lambda t: (t.wbs_code or ""))
        if tasks:
            cum_planned, cum_actual, labels = [], [], []
            run_p = run_a = 0.0
            for t in tasks:
                run_p += float(t.planned_cost or 0)
                run_a += float(t.actual_cost or 0)
                cum_planned.append(run_p); cum_actual.append(run_a); labels.append(t.phase or t.wbs_code)
            remaining = [e.bac - x for x in cum_planned]
            bd = go.Figure()
            bd.add_trace(go.Scatter(x=labels, y=remaining, name="Planned remaining budget", mode="lines+markers"))
            bd.add_trace(go.Scatter(x=labels, y=[e.bac - x for x in cum_actual], name="Actual remaining budget",
                                    mode="lines+markers"))
            bd.update_layout(title="Burn-down (remaining budget)", height=340, margin=dict(t=40))
            st.plotly_chart(bd, use_container_width=True)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**AI Executive Summary**")
            st.info(executive_summary(p, e))
        with col_b:
            st.markdown("**Schedule Delay Signal**")
            st.warning(predict_schedule_delay(e))

        # Upcoming milestones
        ms = sorted([x for x in p.milestones if x.status != "Done"], key=lambda x: (x.due_date or ""))
        if ms:
            st.markdown("**Upcoming Milestones**")
            st.dataframe(pd.DataFrame([{"Milestone": x.name, "Due": x.due_date, "Status": x.status}
                                       for x in ms]), use_container_width=True, hide_index=True)
