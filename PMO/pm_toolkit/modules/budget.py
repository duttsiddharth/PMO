"""Budget Management + Financial Dashboard: planned vs actual, burn rate, forecast."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core import models as m
from modules.common import project_picker, get_session, project_evm, section_title


def render():
    section_title("Budget & Financial Dashboard", "Planned vs actual, monthly spend, forecast and EVM")
    p = project_picker(key="budget_proj")
    s = get_session()
    e = project_evm(p)

    lines = p.budget_lines
    bdf = pd.DataFrame([{ "Category": b.category, "Description": b.description, "Month": b.month,
                          "Planned": b.planned, "Actual": b.actual, "Forecast": b.forecast}
                        for b in lines])

    k = st.columns(4)
    k[0].metric("Budget (BAC)", f"{e.bac:,.0f}")
    k[1].metric("Actual to date", f"{bdf['Actual'].sum():,.0f}" if not bdf.empty else "0")
    k[2].metric("Forecast", f"{bdf['Forecast'].sum():,.0f}" if not bdf.empty else "0")
    k[3].metric("CPI", f"{e.cpi:.2f}")

    if bdf.empty:
        st.info("No budget lines yet.")
        return

    col1, col2 = st.columns(2)
    by_cat = bdf.groupby("Category")[["Planned", "Actual"]].sum().reset_index()
    fig1 = px.bar(by_cat, x="Category", y=["Planned", "Actual"], barmode="group",
                  title="Planned vs Actual by Category",
                  color_discrete_map={"Planned": "#2563EB", "Actual": "#F59E0B"})
    fig1.update_layout(height=340, margin=dict(t=40))
    col1.plotly_chart(fig1, use_container_width=True)

    by_month = bdf.groupby("Month")[["Planned", "Actual", "Forecast"]].sum().reset_index().sort_values("Month")
    by_month["Cumulative Actual"] = by_month["Actual"].cumsum()
    fig2 = go.Figure()
    fig2.add_bar(x=by_month["Month"], y=by_month["Actual"], name="Monthly spend")
    fig2.add_trace(go.Scatter(x=by_month["Month"], y=by_month["Cumulative Actual"],
                              name="Cumulative (burn)", mode="lines+markers", yaxis="y2"))
    fig2.update_layout(title="Monthly Spend & Burn Rate", height=340, margin=dict(t=40),
                       yaxis2=dict(overlaying="y", side="right", showgrid=False))
    col2.plotly_chart(fig2, use_container_width=True)

    # EVM mini-panel
    st.markdown("**Earned Value Snapshot**")
    evm_df = pd.DataFrame([{ "PV": e.pv, "EV": e.ev, "AC": e.ac, "SV": e.sv, "CV": e.cv,
                             "SPI": e.spi, "CPI": e.cpi, "EAC": e.eac, "VAC": e.vac}])
    st.dataframe(evm_df, use_container_width=True, hide_index=True)

    with st.expander("Add budget line"):
        with st.form("add_budget"):
            c = st.columns(4)
            cat = c[0].selectbox("Category", ["Hardware", "Software", "Travel", "Services", "Labour"])
            desc = c[1].text_input("Description")
            month = c[2].text_input("Month (YYYY-MM)")
            planned = c[3].number_input("Planned", min_value=0.0, step=1000.0)
            actual = c[0].number_input("Actual", min_value=0.0, step=1000.0)
            forecast = c[1].number_input("Forecast", min_value=0.0, step=1000.0)
            if st.form_submit_button("Add"):
                s.add(m.BudgetLine(project_id=p.id, category=cat, description=desc, month=month,
                                   planned=planned, actual=actual, forecast=forecast))
                s.commit(); st.rerun()
