"""Reports: export full project datasets to Excel/CSV, and project summary to PDF."""
import pandas as pd
import streamlit as st

from modules.common import project_picker, project_evm, section_title
from reporting.excel_report import build_excel
from reporting.pdf_report import build_status_pdf


def _project_frames(p):
    f = {}
    f["WBS"] = pd.DataFrame([{ "WBS": t.wbs_code, "Task": t.name, "Phase": t.phase, "Owner": t.owner,
                              "Start": t.start_date, "End": t.end_date, "Planned": t.planned_cost,
                              "Actual": t.actual_cost, "%": t.percent_complete, "Status": t.status}
                             for t in p.tasks])
    f["RAID"] = pd.DataFrame([{ "Category": r.category, "Title": r.title, "Owner": r.owner,
                               "Severity": r.severity, "Prob": r.probability, "Impact": r.impact,
                               "Score": r.risk_score, "Status": r.status} for r in p.raid])
    f["Budget"] = pd.DataFrame([{ "Category": b.category, "Month": b.month, "Planned": b.planned,
                                 "Actual": b.actual, "Forecast": b.forecast} for b in p.budget_lines])
    f["Changes"] = pd.DataFrame([{ "CR": c.cr_number, "Description": c.description, "Status": c.status,
                                  "Cost Impact": c.cost_impact, "Schedule days": c.schedule_impact_days}
                                 for c in p.changes])
    f["Migration"] = pd.DataFrame([{ "Type": x.migration_type, "Site": x.site, "Status": x.status,
                                    "Acceptance": x.acceptance} for x in p.migrations])
    f["Stakeholders"] = pd.DataFrame([{ "Name": x.name, "Org": x.org, "RACI": x.raci} for x in p.stakeholders])
    return f


def render():
    section_title("Reports & Exports", "Export full project datasets and summary documents")
    p = project_picker(key="reports_proj")
    e = project_evm(p)
    frames = _project_frames(p)

    st.markdown("**Dataset preview**")
    which = st.selectbox("Dataset", list(frames.keys()))
    st.dataframe(frames[which], use_container_width=True, hide_index=True)

    st.markdown("**Downloads**")
    c1, c2, c3 = st.columns(3)
    c1.download_button("Full workbook (Excel)", build_excel(frames),
                       f"{p.code}_full.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    csv = frames[which].to_csv(index=False).encode()
    c2.download_button(f"{which} (CSV)", csv, f"{p.code}_{which}.csv", "text/csv")

    summary = dict(
        project=p.name, customer=p.customer, week="",
        exec_summary=(f"{p.name} for {p.customer}. Status {p.status}, health {p.health}. "
                      f"{e.percent_complete:.0f}% complete; SPI {e.spi:.2f}; CPI {e.cpi:.2f}; "
                      f"AC {e.ac:,.0f} of BAC {e.bac:,.0f}; EAC {e.eac:,.0f}."),
        completed=[t.name for t in p.tasks if (t.percent_complete or 0) >= 100][:8],
        upcoming=[t.name for t in p.tasks if 0 < (t.percent_complete or 0) < 100][:8],
        risks=[r.title for r in p.raid if r.category == "Risk" and r.status == "Open"][:8],
        issues=[r.title for r in p.raid if r.category == "Issue" and r.status == "Open"][:8],
        budget_status=f"CPI {e.cpi:.2f}; CV {e.cv:,.0f}", schedule_status=f"SPI {e.spi:.2f}; SV {e.sv:,.0f}",
        decisions=[c.description for c in p.changes if c.status in ("Submitted", "Under Review")][:6],
    )
    c3.download_button("Project summary (PDF)", build_status_pdf(summary),
                       f"{p.code}_summary.pdf", "application/pdf")
