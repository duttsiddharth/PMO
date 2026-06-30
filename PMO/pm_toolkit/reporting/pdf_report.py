"""PDF weekly status report generator (ReportLab)."""
import io
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem,
)

PRIMARY = colors.HexColor("#2563EB")


def _styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("H", parent=ss["Heading2"], textColor=PRIMARY, spaceBefore=10))
    ss.add(ParagraphStyle("TitleC", parent=ss["Title"], textColor=colors.HexColor("#0F172A")))
    return ss


def _bullets(items, style):
    if not items:
        return Paragraph("None.", style)
    return ListFlowable([ListItem(Paragraph(str(i), style)) for i in items], bulletType="bullet")


def build_status_pdf(report: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm,
                            leftMargin=18 * mm, rightMargin=18 * mm)
    ss = _styles()
    body = ss["BodyText"]
    flow = []

    flow.append(Paragraph(f"Weekly Status Report — {report.get('project','')}", ss["TitleC"]))
    meta = Table([[f"Customer: {report.get('customer','')}",
                   f"Week ending: {report.get('week', date.today())}",
                   "SD Advisory"]], colWidths=[60 * mm, 60 * mm, 50 * mm])
    meta.setStyle(TableStyle([
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    flow.append(meta)

    flow.append(Paragraph("Executive Summary", ss["H"]))
    flow.append(Paragraph(report.get("exec_summary", ""), body))

    for title, key in [("Completed This Period", "completed"),
                       ("Planned Next Period", "upcoming"),
                       ("Key Risks", "risks"), ("Open Issues", "issues")]:
        flow.append(Paragraph(title, ss["H"]))
        flow.append(_bullets(report.get(key, []), body))

    flow.append(Paragraph("Budget Status", ss["H"]))
    flow.append(Paragraph(report.get("budget_status", ""), body))
    flow.append(Paragraph("Schedule Status", ss["H"]))
    flow.append(Paragraph(report.get("schedule_status", ""), body))
    flow.append(Paragraph("Decisions Required", ss["H"]))
    flow.append(_bullets(report.get("decisions", []), body))

    flow.append(Spacer(1, 8 * mm))
    doc.build(flow)
    buf.seek(0)
    return buf.getvalue()
