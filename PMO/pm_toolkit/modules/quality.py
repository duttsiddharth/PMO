"""Quality Management, Customer Acceptance and Lessons Learned modules."""
import pandas as pd
import streamlit as st

from core import models as m
from modules.common import project_picker, get_session, section_title, project_evm


# ---- Quality -------------------------------------------------------------
def render_quality():
    section_title("Quality Management", "Audit findings, NCRs, corrective & preventive actions")
    p = project_picker(key="qual_proj")
    s = get_session()
    df = pd.DataFrame([{ "Type": q.item_type, "Finding": q.finding, "Owner": q.owner,
                         "Corrective": q.corrective_action, "Preventive": q.preventive_action,
                         "Status": q.status} for q in p.quality])
    st.dataframe(df, use_container_width=True, hide_index=True)
    with st.expander("Add quality item"):
        with st.form("add_q"):
            itype = st.selectbox("Type", ["Audit", "NCR", "CAPA", "Acceptance"])
            finding = st.text_area("Finding")
            corr = st.text_area("Corrective action")
            prev = st.text_area("Preventive action")
            owner = st.text_input("Owner")
            status = st.selectbox("Status", ["Open", "Closed"])
            if st.form_submit_button("Add") and finding:
                s.add(m.QualityItem(project_id=p.id, item_type=itype, finding=finding,
                                    corrective_action=corr, preventive_action=prev,
                                    owner=owner, status=status))
                s.commit(); st.rerun()


# ---- Customer Acceptance -------------------------------------------------
def render_acceptance():
    section_title("Customer Acceptance", "UAT, acceptance certificate, handover and closure")
    p = project_picker(key="acc_proj")
    e = project_evm(p)

    migrated = sum(1 for x in p.migrations if x.status == "Migrated")
    accepted = sum(1 for x in p.migrations if x.acceptance == "Accepted")
    k = st.columns(3)
    k[0].metric("Project complete", f"{e.percent_complete:.0f}%")
    k[1].metric("Sites migrated", migrated)
    k[2].metric("Sites accepted", accepted)

    st.markdown("**Handover Checklist**")
    checklist = ["As-built documentation delivered", "Operational runbooks handed over",
                 "UAT executed and signed", "Support model transitioned",
                 "Open issues below agreed threshold", "Knowledge transfer complete"]
    for item in checklist:
        st.checkbox(item, key=f"hand_{item}")

    st.markdown("**Acceptance Certificate (preview)**")
    st.info(
        f"This certifies that the deliverables for **{p.name}** ({p.code}) provided to "
        f"**{p.customer}** have been reviewed and accepted in accordance with the agreed "
        f"success criteria. Project completion: {e.percent_complete:.0f}%. "
        f"Prepared by SD Advisory. (Generate the formal document from the Reports page.)"
    )


# ---- Lessons Learned -----------------------------------------------------
def render_lessons():
    section_title("Lessons Learned Repository", "Successes, challenges, recommendations and best practices")
    p = project_picker(key="lesson_proj")
    s = get_session()
    df = pd.DataFrame([{ "Category": l.category, "Summary": l.summary, "Detail": l.detail}
                       for l in p.lessons])
    st.dataframe(df, use_container_width=True, hide_index=True)
    with st.expander("Add lesson"):
        with st.form("add_lesson"):
            cat = st.selectbox("Category", ["Success", "Challenge", "Recommendation", "Best Practice"])
            summary = st.text_input("Summary")
            detail = st.text_area("Detail")
            if st.form_submit_button("Add") and summary:
                s.add(m.LessonLearned(project_id=p.id, category=cat, summary=summary, detail=detail))
                s.commit(); st.rerun()
