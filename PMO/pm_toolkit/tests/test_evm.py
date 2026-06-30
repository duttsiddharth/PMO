"""Unit tests for the EVM engine."""
from dataclasses import dataclass

from core.evm import compute_evm, health_from_indices


@dataclass
class Task:
    planned_cost: float
    actual_cost: float
    percent_complete: float


def test_empty_tasks():
    r = compute_evm([])
    assert r.pv == 0 and r.ev == 0 and r.ac == 0
    assert r.spi == 0 and r.cpi == 0  # safe-divide guards


def test_on_track_project():
    tasks = [Task(1000, 500, 50), Task(1000, 500, 50)]
    r = compute_evm(tasks, budget_at_completion=2000)
    assert r.pv == 2000
    assert r.ev == 1000          # 50% of 2000 planned
    assert r.ac == 1000
    assert r.spi == 0.5          # ev/pv
    assert r.cpi == 1.0          # ev/ac
    assert r.cv == 0.0


def test_over_budget_behind():
    tasks = [Task(1000, 1500, 40)]
    r = compute_evm(tasks, 1000)
    assert r.ev == 400
    assert r.cpi < 1             # over budget
    assert r.spi < 1             # behind schedule
    assert r.cv < 0


def test_eac_uses_cpi():
    tasks = [Task(1000, 800, 50)]   # ev=500, cpi=0.625
    r = compute_evm(tasks, 1000)
    assert round(r.eac, 0) == round(1000 / r.cpi, 0)


def test_health_thresholds():
    assert health_from_indices(1.0, 1.0) == "Green"
    assert health_from_indices(0.9, 0.95) == "Amber"
    assert health_from_indices(0.7, 0.8) == "Red"
