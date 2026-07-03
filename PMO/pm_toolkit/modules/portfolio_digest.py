"""Portfolio Weekly Digest: the Monday-morning view for a delivery head.

One page that answers, without chasing anyone: what is the true health,
schedule/cost position and risk exposure of every project this week — plus an
AI (or deterministic) narrative and a copy-ready email digest.

Purely additive module: reads existing models via existing helpers, writes
nothing, so it cannot affect any other part of the toolkit.
"""
from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.ai import portfolio_summary
from core.snapshots import capture_snapshot, ensure_daily_snapshot, snapshot_history
from modules.common import list_projects, project_evm, section_title, rag_badge
from modules.theme import style_fig


def _portfolio_rows():
    rows = []
    for p in list_projects():
        e = project_evm(p)
        rows.append(dict(
            code=p.code, name=p.name, customer=p.customer or "",
            health=p.health, status=p.status,
            spi=round(e.spi, 2), cpi=round(e.cpi, 2),
            pct=e.percent_complete, bac=e.bac, ac=e.ac,
            open_risks=sum(1 for r in p.raid if r.category == "Risk" and r.status == "Open"),
            open_issues=sum(1 for r in p.raid if r.category == "Issue" and r.status == "Open"),
            _project=p,
        ))
    return rows


def _top_risks(rows, limit=8):
    items = []
    for r in rows:
        for it in r["_project"].raid:
            if it.category == "Risk" and it.status == "Open":
                items.append((getattr(it, "risk_score", 0) or 0, r["code"], it.title,
                              getattr(it, "owner", "") or ""))
    items.sort(reverse=True)
    return items[:limit]


def _slipped_milestones(rows, limit=8):
    today = date.today()
    slipped = []
    for r in rows:
        for ms in r["_project"].milestones:
            if ms.due_date and ms.due_date < today and (ms.status or "") not in ("Complete", "Completed", "Done"):
                slipped.append(((today - ms.due_date).days, r["code"], ms.name, str(ms.due_date)))
    slipped.sort(reverse=True)
    return slipped[:limit]


def _email_text(narrative, rows, risks, slipped):
    lines = [f"Subject: Portfolio Weekly Digest — week ending {date.today()}", "",
             narrative, "", "Project positions:"]
    for r in rows:
        lines.append(f"  {r['code']} | {r['health']:>5} | {r['status']:<9} | "
                     f"{r['pct']:>3.0f}% | SPI {r['spi']:.2f} | CPI {r['cpi']:.2f} | "
                     f"Risks {r['open_risks']} | Issues {r['open_issues']}")
    if risks:
        lines += ["", "Top open risks:"]
        lines += [f"  [{c}] {t} (score {s}, owner: {o or 'unassigned'})" for s, c, t, o in risks]
    if slipped:
        lines += ["", "Slipped milestones:"]
        lines += [f"  [{c}] {n} — due {d}, {days} day(s) overdue" for days, c, n, d in slipped]
    return "\n".join(lines)


def render():
    section_title("Portfolio Weekly Digest",
                  "One Monday-morning view of every project — no chasing required")
    rows = _portfolio_rows()
    if not rows:
        st.info("No projects yet. Seed sample data from the Settings page.")
        return

    reds = sum(1 for r in rows if r["health"] == "Red")
    ambers = sum(1 for r in rows if r["health"] == "Amber")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Projects", len(rows))
    c2.metric("Red / Amber", f"{reds} / {ambers}")
    c3.metric("Open Risks", sum(r["open_risks"] for r in rows))
    c4.metric("Open Issues", sum(r["open_issues"] for r in rows))

    st.markdown("#### This week's narrative")
    clean = [{k: v for k, v in r.items() if k != "_project"} for r in rows]
    narrative = portfolio_summary(clean)
    st.write(narrative)

    st.markdown("#### Project positions")
    df = pd.DataFrame(clean)[["code", "name", "customer", "health", "status",
                              "pct", "spi", "cpi", "open_risks", "open_issues"]]
    df.columns = ["Code", "Project", "Customer", "Health", "Status",
                  "% Complete", "SPI", "CPI", "Risks", "Issues"]
    st.dataframe(df, use_container_width=True, hide_index=True)

    left, right = st.columns(2)
    risks = _top_risks(rows)
    slipped = _slipped_milestones(rows)
    with left:
        st.markdown("#### Top open risks")
        if risks:
            for s, c, t, o in risks:
                st.markdown(f"- **[{c}]** {t} — score {s}" + (f", owner {o}" if o else ""))
        else:
            st.caption("No open risks across the portfolio.")
    with right:
        st.markdown("#### Slipped milestones")
        if slipped:
            for days, c, n, d in slipped:
                st.markdown(f"- **[{c}]** {n} — due {d} ({days}d overdue)")
        else:
            st.caption("No overdue milestones.")

    st.markdown("#### Trends over time")
    # Capture at most one automatic snapshot per day; button forces a refresh.
    ensure_daily_snapshot()
    tc1, tc2 = st.columns([3, 1])
    tc2.button("📸 Capture snapshot now", key="snap_now",
               on_click=lambda: capture_snapshot(),
               help="Refreshes today's snapshot. One row per project per day — safe to click repeatedly.")
    hist = snapshot_history()
    dfh = pd.DataFrame([dict(Date=h.snap_date, Project=h.project_code, SPI=h.spi,
                             CPI=h.cpi, Complete=h.percent_complete,
                             Risks=h.open_risks, Issues=h.open_issues) for h in hist])
    n_days = dfh["Date"].nunique() if not dfh.empty else 0
    tc1.caption(f"{n_days} snapshot day(s) recorded. Trends become meaningful after a "
                f"few weeks of history — the app captures one snapshot automatically "
                f"per day this page is opened.")

    if n_days >= 2:
        left, right = st.columns(2)
        with left:
            with st.container(border=True):
                port = dfh.groupby("Date")[["SPI", "CPI"]].mean().reset_index()
                fig = go.Figure()
                fig.add_scatter(x=port["Date"], y=port["SPI"], name="SPI (avg)", mode="lines+markers")
                fig.add_scatter(x=port["Date"], y=port["CPI"], name="CPI (avg)", mode="lines+markers")
                fig.add_hline(y=1.0, line_dash="dot", line_color="#94A3B8")
                fig.update_layout(title="Portfolio schedule & cost performance")
                st.plotly_chart(style_fig(fig, height=320), use_container_width=True)
        with right:
            with st.container(border=True):
                metric = st.selectbox("Metric", ["SPI", "CPI", "Complete"], key="trend_metric",
                                      label_visibility="collapsed")
                fig2 = go.Figure()
                for code, grp in dfh.groupby("Project"):
                    fig2.add_scatter(x=grp["Date"], y=grp[metric], name=code, mode="lines+markers")
                if metric in ("SPI", "CPI"):
                    fig2.add_hline(y=1.0, line_dash="dot", line_color="#94A3B8")
                fig2.update_layout(title=f"{metric} by project")
                st.plotly_chart(style_fig(fig2, height=280), use_container_width=True)
    else:
        st.info("First snapshot captured today. Trend charts appear automatically "
                "once a second day of history exists.")

    st.markdown("#### Send it")
    email = _email_text(narrative, clean, risks, slipped)
    st.text_area("Copy-ready email digest", email, height=220)
    st.download_button("Download digest (.txt)", email,
                       f"portfolio_digest_{date.today()}.txt", "text/plain")
