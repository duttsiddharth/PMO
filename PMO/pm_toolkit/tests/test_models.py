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
    assert len(projects) == 4
    assert all(p.customer == "Meridian Group" for p in projects)
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


def test_portfolio_digest_offline():
    """Digest must work with no API key and produce a complete email text."""
    from core.seed import seed
    seed()
    from core.ai import portfolio_summary
    from modules.portfolio_digest import (_portfolio_rows, _top_risks,
                                          _slipped_milestones, _email_text)
    rows = _portfolio_rows()
    assert len(rows) == 4
    clean = [{k: v for k, v in r.items() if k != "_project"} for r in rows]
    narrative = portfolio_summary(clean)
    assert narrative and len(narrative) > 50
    email = _email_text(narrative, clean, _top_risks(rows), _slipped_milestones(rows))
    assert "Portfolio Weekly Digest" in email and "PRJ-WAN-001" in email


def test_snapshot_capture_idempotent():
    """Snapshots upsert per (date, project): repeated captures never duplicate."""
    from datetime import date, timedelta
    from core.seed import seed
    from core.database import Session
    from core import models as m
    from core.snapshots import capture_snapshot, ensure_daily_snapshot, snapshot_history

    seed()
    n = capture_snapshot()
    assert n == 4
    capture_snapshot()               # same day again — must upsert, not duplicate
    capture_snapshot()
    s = Session()
    today_rows = s.query(m.PortfolioSnapshot).filter(
        m.PortfolioSnapshot.snap_date == date.today()).count()
    assert today_rows == 4
    assert ensure_daily_snapshot() is False   # today already captured

    # A second (historical) day makes trend history span two dates
    capture_snapshot(date.today() - timedelta(days=7))
    hist = snapshot_history()
    assert len(hist) == 8
    assert len({h.snap_date for h in hist}) == 2
    assert all(h.spi >= 0 and h.cpi >= 0 for h in hist)
