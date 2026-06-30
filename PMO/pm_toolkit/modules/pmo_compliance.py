"""PMO Compliance Dashboard: artifact completion tracking with compliance %."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from modules.common import project_picker, get_session, section_title, list_projects


def render():
    section_title("PMO Compliance Dashboard", "Governance artifact completion across projects")

    # Portfolio compliance bar
    rows = []
    for p in list_projects():
        total = len(p.compliance) or 1
        done = sum(1 for c in p.compliance if c.complete)
        rows.append({"Project": p.code, "Compliance %": round(done / total * 100, 0)})
    if rows:
        pdf = pd.DataFrame(rows)
        fig = go.Figure(go.Bar(x=pdf["Project"], y=pdf["Compliance %"], marker_color="#2563EB"))
        fig.update_layout(title="Portfolio PMO Compliance %", height=300, margin=dict(t=40),
                          yaxis=dict(range=[0, 100]))
        st.plotly_chart(fig, use_container_width=True)

    p = project_picker(key="pmo_proj")
    s = get_session()
    total = len(p.compliance) or 1
    done = sum(1 for c in p.compliance if c.complete)
    st.metric("Compliance", f"{done/total*100:.0f}%", help=f"{done} of {total} artifacts complete")

    st.markdown("**Artifact Checklist** (toggle to update)")
    changed = False
    for c in p.compliance:
        val = st.checkbox(c.artifact, value=c.complete, key=f"comp_{c.id}")
        if val != c.complete:
            c.complete = val
            changed = True
    if changed:
        s.commit()
        st.rerun()
