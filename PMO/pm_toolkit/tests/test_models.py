"""Integration-style tests: seed the DB and validate relationships + reports."""
import os

# Force an isolated test database before importing engine-bound modules.
os.environ["PM_DATABASE_URL"] = "sqlite:///:memory:"


def test_seed_and_relationships():
    from core.seed import seed
    from core.database import Session
    from core import models as m

    seed()
    s = Session()
    projects = s.query(m.Project).all()
    assert len(projects) == 3
    p = projects[0]
    assert len(p.tasks) >= 6
    assert len(p.raid) >= 5
    assert any(r.category == "Risk" for r in p.raid)
    assert len(p.compliance) == 12
    s.close()


def test_reports_build():
    from reporting.excel_report import build_excel
    from reporting.word_report import build_status_docx
    from reporting.pdf_report import build_status_pdf
    from reporting.ppt_report import build_status_pptx
    import pandas as pd

    report = dict(project="Test", customer="Cust", week="2026-06-30",
                  exec_summary="Summary", completed=["a"], upcoming=["b"],
                  risks=["r"], issues=["i"], budget_status="ok",
                  schedule_status="ok", decisions=["d"])
    assert build_status_pdf(report)[:4] == b"%PDF"
    assert len(build_status_docx(report)) > 0
    assert len(build_status_pptx(report)) > 0
    assert len(build_excel({"S": pd.DataFrame({"x": [1]})})) > 0
