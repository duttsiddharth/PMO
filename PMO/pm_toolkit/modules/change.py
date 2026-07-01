"""Change Management: change requests with cost/schedule impact and approval workflow."""
import pandas as pd
import streamlit as st

from core import models as m
from modules.common import project_picker, get_session, section_title
from core.crud import editable_grid

STATUSES = ["Submitted", "Under Review", "Approved", "Rejected"]


def render():
    section_title("Change Management", "Change requests, impact assessment and approval workflow")
    p = project_picker(key="change_proj")
    s = get_session()

    with st.expander("✏️ Edit change requests (inline grid: add / edit / delete)"):
        editable_grid(m.ChangeRequest, scope_fk="project_id", scope_id=p.id, key=f"cr_grid_{p.id}")

    df = pd.DataFrame([{ "CR #": c.cr_number, "Description": c.description,
                         "Scope Impact": c.scope_impact, "Cost Impact": c.cost_impact,
                         "Schedule (days)": c.schedule_impact_days, "Raised by": c.raised_by,
                         "Approver": c.approver, "Status": c.status, "Raised": c.raised_on}
                       for c in p.changes])
    if not df.empty:
        k = st.columns(4)
        k[0].metric("Total CRs", len(df))
        k[1].metric("Approved", int((df["Status"] == "Approved").sum()))
        k[2].metric("Pending", int(df["Status"].isin(["Submitted", "Under Review"]).sum()))
        k[3].metric("Approved cost impact", f"{df[df['Status']=='Approved']['Cost Impact'].sum():,.0f}")
    st.dataframe(df, width='stretch', hide_index=True)

    # Update workflow status
    if p.changes:
        st.markdown("**Update CR status**")
        cr_map = {c.cr_number: c for c in p.changes}
        c1, c2, c3 = st.columns([2, 2, 1])
        sel = c1.selectbox("CR", list(cr_map.keys()))
        new_status = c2.selectbox("New status", STATUSES)
        if c3.button("Apply"):
            cr_map[sel].status = new_status
            s.commit(); st.rerun()

    with st.expander("Raise new change request"):
        with st.form("add_cr"):
            num = st.text_input("CR number")
            desc = st.text_area("Description")
            just = st.text_area("Business justification")
            c = st.columns(3)
            scope = c[0].text_input("Scope impact")
            cost = c[1].number_input("Cost impact", min_value=0.0, step=1000.0)
            sched = c[2].number_input("Schedule impact (days)", min_value=0, step=1)
            raised_by = c[0].text_input("Raised by")
            approver = c[1].text_input("Approver")
            if st.form_submit_button("Submit CR") and num:
                s.add(m.ChangeRequest(project_id=p.id, cr_number=num, description=desc,
                                      justification=just, scope_impact=scope, cost_impact=cost,
                                      schedule_impact_days=int(sched), raised_by=raised_by,
                                      approver=approver, status="Submitted"))
                s.commit(); st.rerun()
