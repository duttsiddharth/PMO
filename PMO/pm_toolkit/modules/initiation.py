"""Project Initiation: Charter, Business Case, Stakeholder Register, RACI Matrix."""
import pandas as pd
import streamlit as st

from core import models as m
from modules.common import project_picker, get_session, section_title


def render():
    section_title("Project Initiation", "Charter, business case, stakeholders and RACI")
    p = project_picker(key="init_proj")
    s = get_session()

    tab_charter, tab_stake, tab_raci = st.tabs(["Charter & Business Case", "Stakeholder Register", "RACI Matrix"])

    with tab_charter:
        with st.form("charter"):
            c1, c2 = st.columns(2)
            business_case = c1.text_area("Business Case", p.business_case or "", height=110)
            scope = c2.text_area("Scope", p.scope or "", height=110)
            objectives = c1.text_area("Objectives", p.objectives or "", height=90)
            deliverables = c2.text_area("Deliverables", p.deliverables or "", height=90)
            assumptions = c1.text_area("Assumptions", p.assumptions or "", height=90)
            constraints = c2.text_area("Constraints", p.constraints or "", height=90)
            success = st.text_area("Success Criteria", p.success_criteria or "", height=80)
            if st.form_submit_button("Save Charter"):
                p.business_case, p.scope = business_case, scope
                p.objectives, p.deliverables = objectives, deliverables
                p.assumptions, p.constraints = assumptions, constraints
                p.success_criteria = success
                s.commit()
                st.success("Charter saved.")

    with tab_stake:
        st.markdown("**Stakeholder Register**")
        data = pd.DataFrame([{ "Name": x.name, "Org": x.org, "Role": x.role,
                               "Influence": x.influence, "Interest": x.interest,
                               "RACI": x.raci, "Contact": x.contact} for x in p.stakeholders])
        st.dataframe(data, width='stretch', hide_index=True)
        with st.expander("Add stakeholder"):
            with st.form("add_stake"):
                cols = st.columns(3)
                name = cols[0].text_input("Name")
                org = cols[1].text_input("Organisation")
                role = cols[2].text_input("Role")
                infl = cols[0].selectbox("Influence", ["Low", "Medium", "High"])
                inter = cols[1].selectbox("Interest", ["Low", "Medium", "High"])
                raci = cols[2].selectbox("RACI", ["R", "A", "C", "I"])
                contact = st.text_input("Contact")
                if st.form_submit_button("Add") and name:
                    s.add(m.Stakeholder(project_id=p.id, name=name, org=org, role=role,
                                        influence=infl, interest=inter, raci=raci, contact=contact))
                    s.commit(); st.rerun()

    with tab_raci:
        st.caption("RACI = Responsible / Accountable / Consulted / Informed")
        raci_df = pd.DataFrame([{ "Stakeholder": x.name, "Role": x.role, "RACI": x.raci}
                                for x in p.stakeholders])
        st.dataframe(raci_df, width='stretch', hide_index=True)
