"""Weekly Status Report Generator with AI summary and PDF/Word/PPTX/Excel export."""
from datetime import date

import pandas as pd
import streamlit as st

from core.ai import executive_summary
from modules.common import project_picker, project_evm, section_title
from reporting.pdf_report import build_status_pdf
from reporting.word_report import build_status_docx
from reporting.ppt_report import build_status_pptx
from reporting.excel_report import build_excel


def _gather(p, e):
    completed = [t.name for t in p.tasks if t.percent_complete and t.percent_complete >= 100][:6]
    upcoming = [t.name for t in p.tasks if 0 < (t.percent_complete or 0) < 100][:6]
    risks = [f"{r.title} (sev {r.severity})" for r in p.raid
             if r.category == "Risk" and r.status == "Open"][:6]
    issues = [r.title for r in p.raid if r.category == "Issue" and r.status == "Open"][:6]
    decisions = []
    for mtg in p.meetings:
        decisions += [a.description for a in mtg.action_items if a.status == "Open"]
    schedule = ("Ahead of schedule" if e.spi >= 1 else "Behind schedule") + f" (SPI {e.spi:.2f}, SV {e.sv:,.0f})"
    budget = ("Under budget" if e.cpi >= 1 else "Over budget") + \
             f" (CPI {e.cpi:.2f}, AC {e.ac:,.0f} of BAC {e.bac:,.0f}, EAC {e.eac:,.0f})"
    return dict(
        project=p.name, customer=p.customer, week=str(date.today()),
        exec_summary=executive_summary(p, e),
        completed=completed or ["Mobilisation activities in progress"],
        upcoming=upcoming or ["Continue build / migration workstream"],
        risks=risks or ["No open risks"], issues=issues or ["No open issues"],
        budget_status=budget, schedule_status=schedule,
        decisions=decisions[:6] or ["No outstanding decisions"],
    )


def render():
    section_title("Weekly Status Report", "Auto-generated executive report with multi-format export")
    p = project_picker(key="status_proj")
    e = project_evm(p)
    report = _gather(p, e)

    st.markdown("#### Preview")
    st.markdown(f"**{report['project']}** — {report['customer']} — week ending {report['week']}")
    st.markdown("**Executive Summary**")
    st.write(report["exec_summary"])
    c1, c2 = st.columns(2)
    c1.markdown("**Completed**"); c1.write("\n".join(f"- {x}" for x in report["completed"]))
    c2.markdown("**Upcoming**"); c2.write("\n".join(f"- {x}" for x in report["upcoming"]))
    c1.markdown("**Risks**"); c1.write("\n".join(f"- {x}" for x in report["risks"]))
    c2.markdown("**Issues**"); c2.write("\n".join(f"- {x}" for x in report["issues"]))
    st.markdown(f"**Budget:** {report['budget_status']}")
    st.markdown(f"**Schedule:** {report['schedule_status']}")

    st.markdown("#### Export")
    d1, d2, d3, d4 = st.columns(4)
    fname = f"status_{p.code}_{report['week']}"
    d1.download_button("PDF", build_status_pdf(report), f"{fname}.pdf", "application/pdf")
    d2.download_button("Word", build_status_docx(report), f"{fname}.docx",
                       "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    d3.download_button("PowerPoint", build_status_pptx(report), f"{fname}.pptx",
                       "application/vnd.openxmlformats-officedocument.presentationml.presentation")
    excel_sheets = {
        "Summary": pd.DataFrame([{ "Project": report["project"], "Customer": report["customer"],
                                   "Week": report["week"], "SPI": e.spi, "CPI": e.cpi,
                                   "% Complete": e.percent_complete}]),
        "Completed": pd.DataFrame({"Item": report["completed"]}),
        "Upcoming": pd.DataFrame({"Item": report["upcoming"]}),
        "Risks": pd.DataFrame({"Item": report["risks"]}),
    }
    d4.download_button("Excel", build_excel(excel_sheets), f"{fname}.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
