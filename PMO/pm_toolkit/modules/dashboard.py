"""Executive Dashboard: RAG health, EVM KPIs, burn-down, financial charts."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core import models as m
from core.ai import executive_summary, predict_schedule_delay
from modules.common import (
    list_projects, project_picker, project_evm, section_title,
)
from modules.theme import style_fig, summary_card, rag_pill, RAG, PALETTE_SEQ


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
                         SPI=round(e.spi, 2), CPI=round(e.cpi, 2), AC=e.ac, BAC=e.bac,
                         Risks=open_risks, Issues=open_issues, CRs=open_crs))
    return pd.DataFrame(rows)


def _portfolio(dfp):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Active Projects", len(dfp))
    c2.metric("Open Risks", int(dfp["Risks"].sum()) if not dfp.empty else 0)
    c3.metric("Open Issues", int(dfp["Issues"].sum()) if not dfp.empty else 0)
    c4.metric("Open Change Requests", int(dfp["CRs"].sum()) if not dfp.empty else 0)

    if dfp.empty:
        st.info("No projects yet. Seed sample data from the Settings page.")
        return

    st.write("")
    left, right = st.columns([1, 1.4], gap="medium")

    with left:
        with st.container(border=True):
            health_counts = dfp["Health"].value_counts().reindex(["Green", "Amber", "Red"]).fillna(0)
            fig = go.Figure(data=[go.Pie(
                labels=health_counts.index, values=health_counts.values, hole=0.62,
                marker=dict(colors=[RAG[h] for h in health_counts.index],
                            line=dict(color="#FFFFFF", width=2)),
                textinfo="value", textfont=dict(size=14, color="#fff"))])
            fig.update_layout(title="Portfolio Health (RAG)",
                              annotations=[dict(text=f"{len(dfp)}<br>projects", x=0.5, y=0.5,
                                                font=dict(size=15, color="#0F172A"), showarrow=False)])
            st.plotly_chart(style_fig(fig, height=330), width='stretch',
                            config={"displayModeBar": False})

    with right:
        with st.container(border=True):
            spi_cpi = px.scatter(dfp, x="SPI", y="CPI", text="Project", color="Health",
                                 color_discrete_map=RAG, size="BAC", size_max=44,
                                 title="Schedule vs Cost Performance (SPI × CPI)")
            spi_cpi.add_hline(y=1, line_dash="dot", line_color="#94A3B8")
            spi_cpi.add_vline(x=1, line_dash="dot", line_color="#94A3B8")
            spi_cpi.update_traces(textposition="top center",
                                  textfont=dict(size=10, color="#475569"),
                                  marker=dict(line=dict(width=1, color="#fff")))
            st.plotly_chart(style_fig(spi_cpi, height=330), width='stretch',
                            config={"displayModeBar": False})

    st.write("")
    st.markdown("##### Project Portfolio")
    show = dfp[["Project", "Name", "Customer", "Health", "Status", "Complete",
                "SPI", "CPI", "Risks", "Issues", "CRs"]]
    st.dataframe(
        show, width='stretch', hide_index=True,
        column_config={
            "SPI": st.column_config.NumberColumn(format="%.2f"),
            "CPI": st.column_config.NumberColumn(format="%.2f"),
            "Health": st.column_config.TextColumn("Health"),
        },
    )


def _single_project():
    p = project_picker(key="dash_proj")
    e = project_evm(p)

    with st.container(border=True):
        head = st.columns([3, 1, 1, 1])
        head[0].markdown(f"#### {p.code} — {p.name}")
        head[0].caption(f"{p.customer} · {p.project_type} · {p.region or '—'}")
        head[1].markdown("<div style='font-size:.72rem;color:#64748B;font-weight:600;"
                         "text-transform:uppercase;letter-spacing:.045em'>Health</div>"
                         + rag_pill(p.health), unsafe_allow_html=True)
        head[2].metric("Status", p.status)
        head[3].metric("Complete", f"{e.percent_complete:.0f}%")

    st.write("")
    k = st.columns(4)
    k[0].metric("Earned Value (EV)", f"${e.ev:,.0f}")
    k[1].metric("Planned Value (PV)", f"${e.pv:,.0f}")
    k[2].metric("Actual Cost (AC)", f"${e.ac:,.0f}")
    k[3].metric("Budget (BAC)", f"${e.bac:,.0f}")

    k2 = st.columns(4)
    k2[0].metric("SPI", f"{e.spi:.2f}", delta=f"{(e.spi-1)*100:.0f}%")
    k2[1].metric("CPI", f"{e.cpi:.2f}", delta=f"{(e.cpi-1)*100:.0f}%")
    k2[2].metric("Schedule Variance", f"${e.sv:,.0f}")
    k2[3].metric("Cost Variance", f"${e.cv:,.0f}")

    k3 = st.columns(3)
    k3[0].metric("Estimate at Completion", f"${e.eac:,.0f}")
    k3[1].metric("Estimate to Complete", f"${e.etc:,.0f}")
    k3[2].metric("Variance at Completion", f"${e.vac:,.0f}")

    st.write("")
    tasks = sorted(p.tasks, key=lambda t: (t.wbs_code or ""))
    if tasks:
        with st.container(border=True):
            cum_planned, cum_actual, labels = [], [], []
            run_p = run_a = 0.0
            for t in tasks:
                run_p += float(t.planned_cost or 0)
                run_a += float(t.actual_cost or 0)
                cum_planned.append(run_p); cum_actual.append(run_a)
                labels.append(t.phase or t.wbs_code)
            bd = go.Figure()
            bd.add_trace(go.Scatter(x=labels, y=[e.bac - x for x in cum_planned],
                                    name="Planned remaining", mode="lines+markers",
                                    line=dict(color=PALETTE_SEQ[0], width=3),
                                    fill="tozeroy", fillcolor="rgba(37,99,235,.06)"))
            bd.add_trace(go.Scatter(x=labels, y=[e.bac - x for x in cum_actual],
                                    name="Actual remaining", mode="lines+markers",
                                    line=dict(color="#EF4444", width=3, dash="dot")))
            bd.update_layout(title="Budget Burn-down (remaining budget by phase)",
                             yaxis_title="Remaining ($)")
            st.plotly_chart(style_fig(bd, height=360), width='stretch',
                            config={"displayModeBar": False})

    st.write("")
    col_a, col_b = st.columns(2, gap="medium")
    with col_a:
        summary_card("Executive Summary", executive_summary(p, e), tone="info")
    with col_b:
        delay = predict_schedule_delay(e)
        tone = "success" if e.spi >= 0.95 else ("warning" if e.spi >= 0.85 else "danger")
        summary_card("Schedule Delay Signal", delay, tone=tone)

    ms = sorted([x for x in p.milestones if x.status != "Done"], key=lambda x: (x.due_date or ""))
    if ms:
        st.write("")
        st.markdown("##### Upcoming Milestones")
        st.dataframe(pd.DataFrame([{"Milestone": x.name, "Due": x.due_date, "Status": x.status}
                                   for x in ms]), width='stretch', hide_index=True)


def render():
    section_title("Executive Dashboard", "Portfolio health and earned-value performance")
    tab_port, tab_proj = st.tabs(["Portfolio", "Single Project"])
    with tab_port:
        _portfolio(_portfolio_overview())
    with tab_proj:
        _single_project()
