"""Earned Value Management (EVM) engine.

Computes the standard PMP EVM metrics for a project from its WBS tasks:

    PV (Planned Value)     = sum(task.planned_cost)            -- full BAC of planned work
    EV (Earned Value)      = sum(task.planned_cost * %complete)
    AC (Actual Cost)       = sum(task.actual_cost)
    BAC (Budget at Compl.) = project.budget or sum(planned_cost)

    SV  = EV - PV          (schedule variance; >0 ahead)
    CV  = EV - AC          (cost variance; >0 under budget)
    SPI = EV / PV          (schedule performance index; >1 ahead)
    CPI = EV / AC          (cost performance index; >1 under budget)
    EAC = BAC / CPI        (estimate at completion)
    ETC = EAC - AC         (estimate to complete)
    VAC = BAC - EAC        (variance at completion)

All divisions guard against zero so the engine never raises on empty data.
"""
from dataclasses import dataclass, asdict


@dataclass
class EVMResult:
    pv: float = 0.0
    ev: float = 0.0
    ac: float = 0.0
    bac: float = 0.0
    sv: float = 0.0
    cv: float = 0.0
    spi: float = 0.0
    cpi: float = 0.0
    eac: float = 0.0
    etc: float = 0.0
    vac: float = 0.0
    percent_complete: float = 0.0

    def as_dict(self):
        return asdict(self)


def _safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def compute_evm(tasks, budget_at_completion: float | None = None) -> EVMResult:
    """Compute EVM metrics from an iterable of WBSTask-like objects.

    Each task must expose: planned_cost, actual_cost, percent_complete (0-100).
    """
    pv = sum(float(t.planned_cost or 0) for t in tasks)
    ev = sum(float(t.planned_cost or 0) * float(t.percent_complete or 0) / 100.0 for t in tasks)
    ac = sum(float(t.actual_cost or 0) for t in tasks)
    bac = float(budget_at_completion) if budget_at_completion else pv

    spi = _safe_div(ev, pv)
    cpi = _safe_div(ev, ac)
    eac = _safe_div(bac, cpi) if cpi else bac
    pct = _safe_div(ev, bac) * 100.0

    return EVMResult(
        pv=round(pv, 2), ev=round(ev, 2), ac=round(ac, 2), bac=round(bac, 2),
        sv=round(ev - pv, 2), cv=round(ev - ac, 2),
        spi=round(spi, 3), cpi=round(cpi, 3),
        eac=round(eac, 2), etc=round(eac - ac, 2), vac=round(bac - eac, 2),
        percent_complete=round(pct, 1),
    )


def health_from_indices(spi: float, cpi: float) -> str:
    """Derive a RAG health rating from SPI/CPI thresholds."""
    worst = min(spi or 1.0, cpi or 1.0)
    if worst >= 0.95:
        return "Green"
    if worst >= 0.85:
        return "Amber"
    return "Red"
