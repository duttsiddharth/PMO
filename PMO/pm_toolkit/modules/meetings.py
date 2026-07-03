"""Meeting Management: agenda, attendees, MoM, decisions and action items."""
import pandas as pd
import streamlit as st

from core import models as m
from modules.common import project_picker, get_session, section_title, macd_panel


def render():
    section_title("Meeting Management", "Agenda, minutes, decisions and action tracking")
    p = project_picker(key="meet_proj")
    macd_panel(m.Meeting, scope_fk="project_id", scope_id=p.id,
               key=f"macd_meet_{p.id}", label="Meetings")
    s = get_session()

    for mtg in sorted(p.meetings, key=lambda x: (x.meeting_date or ""), reverse=True):
        with st.expander(f"{mtg.meeting_date} — {mtg.title}", expanded=False):
            st.markdown(f"**Attendees:** {mtg.attendees}")
            st.markdown(f"**Agenda:** {mtg.agenda}")
            st.markdown(f"**Minutes:** {mtg.minutes}")
            st.markdown(f"**Decisions:** {mtg.decisions}")
            if mtg.action_items:
                st.dataframe(pd.DataFrame([{ "Action": a.description, "Owner": a.owner,
                                             "Due": a.due_date, "Status": a.status}
                                           for a in mtg.action_items]),
                             width='stretch', hide_index=True)

    # Open actions across project
    open_actions = []
    for mtg in p.meetings:
        for a in mtg.action_items:
            if a.status == "Open":
                open_actions.append({"Action": a.description, "Owner": a.owner, "Due": a.due_date,
                                     "Meeting": mtg.title})
    if open_actions:
        st.markdown("**All Open Action Items**")
        st.dataframe(pd.DataFrame(open_actions), width='stretch', hide_index=True)

    with st.expander("Log new meeting"):
        with st.form("add_meeting"):
            title = st.text_input("Title")
            mdate = st.date_input("Date")
            attendees = st.text_input("Attendees")
            agenda = st.text_area("Agenda")
            minutes = st.text_area("Minutes (MoM)")
            decisions = st.text_area("Decisions")
            if st.form_submit_button("Save meeting") and title:
                s.add(m.Meeting(project_id=p.id, title=title, meeting_date=mdate,
                                attendees=attendees, agenda=agenda, minutes=minutes,
                                decisions=decisions))
                s.commit(); st.rerun()
