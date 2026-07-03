"""Portfolio snapshot capture for EVM trend history.

Streamlit apps cannot run cron jobs, so snapshots are captured:
  - automatically, at most once per calendar day, when the Portfolio Weekly
    Digest page renders (ensure_daily_snapshot), and
  - on demand via the "Capture snapshot now" button (capture_snapshot,
    which upserts today's rows so repeated clicks never duplicate).

Design principle: additive and idempotent. Reading modules were not modified;
this module only writes to the new portfolio_snapshots table.
"""
from __future__ import annotations

from datetime import date

from core.database import session_scope, Session
from core import models as m
from core.evm import compute_evm


def _project_metrics(p):
    e = compute_evm(p.tasks, p.budget)
    return dict(
        project_id=p.id, project_code=p.code, health=p.health, status=p.status,
        spi=round(e.spi, 4), cpi=round(e.cpi, 4),
        percent_complete=round(e.percent_complete, 2), ac=e.ac, bac=e.bac,
        open_risks=sum(1 for r in p.raid if r.category == "Risk" and r.status == "Open"),
        open_issues=sum(1 for r in p.raid if r.category == "Issue" and r.status == "Open"),
    )


def capture_snapshot(snap_date: date | None = None) -> int:
    """Capture (or refresh) one snapshot row per project for the given date.

    Upsert semantics: existing rows for (snap_date, project_id) are updated,
    so calling this many times in one day never duplicates data.
    Returns the number of projects captured.
    """
    snap_date = snap_date or date.today()
    count = 0
    with session_scope() as s:
        projects = s.query(m.Project).all()
        for p in projects:
            metrics = _project_metrics(p)
            row = (s.query(m.PortfolioSnapshot)
                     .filter(m.PortfolioSnapshot.snap_date == snap_date,
                             m.PortfolioSnapshot.project_id == p.id)
                     .one_or_none())
            if row is None:
                row = m.PortfolioSnapshot(snap_date=snap_date, **metrics)
                s.add(row)
            else:
                for k, v in metrics.items():
                    setattr(row, k, v)
            count += 1
    return count


def ensure_daily_snapshot() -> bool:
    """Capture today's snapshot if none exists yet. Returns True if captured."""
    s = Session()
    exists = (s.query(m.PortfolioSnapshot)
                .filter(m.PortfolioSnapshot.snap_date == date.today())
                .first())
    if exists:
        return False
    capture_snapshot()
    return True


def snapshot_history():
    """All snapshot rows ordered by date, for trend charts."""
    s = Session()
    return (s.query(m.PortfolioSnapshot)
              .order_by(m.PortfolioSnapshot.snap_date, m.PortfolioSnapshot.project_code)
              .all())
