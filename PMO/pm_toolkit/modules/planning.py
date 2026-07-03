"""Project Planning: WBS, Gantt chart, dependencies, critical path, milestones."""
import pandas as pd
import plotly.express as px
import streamlit as st
from modules.theme import style_fig

from core import models as m
from modules.common import project_picker, get_session, section_title, macd_panel


def render():
    section_title("Project Planning", "WBS, schedule, critical path and milestones")
    p = project_picker(key="plan_proj")
    macd_panel(m.WBSTask, scope_fk="project_id", scope_id=p.id,
               key=f"macd_wbs_{p.id}", label="WBS tasks")
    macd_panel(m.Milestone, scope_fk="project_id", scope_id=p.id,
               key=f"macd_ms_{p.id}", label="Milestones")
    s = get_session()

    tab_wbs, tab_gantt, tab_ms = st.tabs(["WBS & Dependencies", "Gantt Chart", "Milestones"])

    with tab_wbs:
        wbs = pd.DataFrame([{ "WBS": t.wbs_code, "Task": t.name, "Phase": t.phase,
                              "Owner": t.owner, "Start": t.start_date, "End": t.end_date,
                              "Depends On": t.depends_on, "Critical": t.is_critical,
                              "Planned": t.planned_cost, "Actual": t.actual_cost,
                              "% Complete": t.percent_complete, "Status": t.status}
                            for t in sorted(p.tasks, key=lambda x: x.wbs_code or "")])
        st.dataframe(wbs, width='stretch', hide_index=True)
        crit = wbs[wbs["Critical"] == True]["Task"].tolist() if not wbs.empty else []
        if crit:
            st.info("**Critical path tasks:** " + " → ".join(crit))

        with st.expander("Add WBS task"):
            with st.form("add_task"):
                c = st.columns(4)
                code = c[0].text_input("WBS code")
                name = c[1].text_input("Task name")
                phase = c[2].text_input("Phase")
                owner = c[3].text_input("Owner")
                start = c[0].date_input("Start")
                end = c[1].date_input("End")
                planned = c[2].number_input("Planned cost", min_value=0.0, step=1000.0)
                pct = c[3].slider("% complete", 0, 100, 0)
                critical = st.checkbox("On critical path")
                if st.form_submit_button("Add task") and name:
                    s.add(m.WBSTask(project_id=p.id, wbs_code=code, name=name, phase=phase,
                                    owner=owner, start_date=start, end_date=end,
                                    planned_cost=planned, percent_complete=pct, is_critical=critical,
                                    status="In Progress" if pct else "Not Started"))
                    s.commit(); st.rerun()

    with tab_gantt:
        rows = [{ "Task": t.name, "Start": t.start_date, "Finish": t.end_date,
                  "Phase": t.phase, "Critical": "Critical" if t.is_critical else "Normal"}
                for t in p.tasks if t.start_date and t.end_date]
        if rows:
            g = pd.DataFrame(rows)
            fig = px.timeline(g, x_start="Start", x_end="Finish", y="Task", color="Critical",
                              color_discrete_map={"Critical": "#DC2626", "Normal": "#2563EB"})
            fig.update_yaxes(autorange="reversed")
            fig.update_layout(height=420, margin=dict(t=20))
            st.plotly_chart(style_fig(fig), width='stretch', config={"displayModeBar": False})
        else:
            st.info("Add task start/end dates to render the Gantt chart.")

    with tab_ms:
        ms = pd.DataFrame([{ "Milestone": x.name, "Due": x.due_date, "Status": x.status}
                           for x in p.milestones])
        st.dataframe(ms, width='stretch', hide_index=True)
        with st.expander("Add milestone"):
            with st.form("add_ms"):
                name = st.text_input("Milestone name")
                due = st.date_input("Due date")
                status = st.selectbox("Status", ["Pending", "In Progress", "Done"])
                if st.form_submit_button("Add") and name:
                    s.add(m.Milestone(project_id=p.id, name=name, due_date=due, status=status))
                    s.commit(); st.rerun()
