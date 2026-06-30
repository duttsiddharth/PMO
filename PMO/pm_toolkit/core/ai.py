"""AI helpers for status summaries, risk prediction and schedule-delay flags.

Design principle: the toolkit must run fully offline. If ANTHROPIC_API_KEY is
configured these helpers call the Anthropic API for richer narratives; if not,
they fall back to deterministic, template-driven output derived from the data
itself. Either way the calling module gets a string back.
"""
from __future__ import annotations

import config


def _anthropic_available() -> bool:
    return bool(config.ANTHROPIC_API_KEY)


def _call_anthropic(prompt: str, system: str = "") -> str | None:
    if not _anthropic_available():
        return None
    try:
        import anthropic  # imported lazily; optional dependency
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model=config.AI_MODEL,
            max_tokens=900,
            system=system or "You are a senior PMP IT infrastructure project manager.",
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()
    except Exception:
        return None


def executive_summary(project, evm) -> str:
    """One-paragraph executive summary; AI if available else templated."""
    prompt = (
        f"Write a concise executive summary (4-6 sentences) for IT infrastructure "
        f"project '{project.name}' ({project.project_type}) for customer "
        f"{project.customer}. Status {project.status}, health {project.health}. "
        f"EVM: SPI {evm.spi}, CPI {evm.cpi}, {evm.percent_complete}% complete, "
        f"AC {evm.ac:,.0f} of BAC {evm.bac:,.0f}. Be factual and board-ready."
    )
    ai = _call_anthropic(prompt)
    if ai:
        return ai

    schedule = "ahead of schedule" if evm.spi >= 1 else "behind schedule"
    cost = "under budget" if evm.cpi >= 1 else "over budget"
    return (
        f"{project.name} ({project.project_type}) for {project.customer} is currently "
        f"{evm.percent_complete:.0f}% complete and rated {project.health}. The project is "
        f"{schedule} (SPI {evm.spi:.2f}) and {cost} (CPI {evm.cpi:.2f}). Actual cost to date "
        f"is {evm.ac:,.0f} against a budget at completion of {evm.bac:,.0f}, with an estimate "
        f"at completion of {evm.eac:,.0f}. Continued focus on the critical path and open RAID "
        f"items is recommended to protect the {project.status.lower()} phase commitments."
    )


def predict_risks(project, raid_items) -> list[str]:
    """Lightweight heuristic risk flags (deterministic)."""
    flags: list[str] = []
    open_high = [r for r in raid_items if r.category == "Risk" and r.status == "Open" and r.risk_score >= 15]
    if open_high:
        flags.append(f"{len(open_high)} high-exposure risk(s) (score >= 15) remain open.")
    open_issues = [r for r in raid_items if r.category == "Issue" and r.status == "Open"]
    if len(open_issues) >= 3:
        flags.append(f"{len(open_issues)} open issues may compound into schedule slippage.")
    if project.health == "Red":
        flags.append("Project RAG is Red — escalate to the steering committee.")
    if not flags:
        flags.append("No elevated risk signals detected from current RAID data.")
    return flags


def predict_schedule_delay(evm) -> str:
    """Flag likely schedule delay from SPI."""
    if evm.spi >= 1.0:
        return "On or ahead of schedule (SPI >= 1.00)."
    severity = "moderate" if evm.spi >= 0.9 else "significant"
    return (
        f"{severity.capitalize()} delay risk: SPI {evm.spi:.2f}. At current performance the "
        f"remaining work will take longer than baselined — replan the critical path."
    )
