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


# --------------------------------------------------------------------------
# Knowledge intake: extract project fields from RFP / SOW / design documents
# --------------------------------------------------------------------------
_KB_FIELDS = ["name", "customer", "project_type", "region", "business_case",
              "scope", "objectives", "deliverables", "assumptions",
              "constraints", "success_criteria"]

_HEADING_MAP = {
    "business_case": ["business case", "background", "introduction", "purpose", "context"],
    "scope": ["scope of work", "scope of services", "scope", "statement of work"],
    "objectives": ["objectives", "goals", "project objectives"],
    "deliverables": ["deliverables", "expected deliverables", "outputs"],
    "assumptions": ["assumptions"],
    "constraints": ["constraints", "limitations", "dependencies and constraints"],
    "success_criteria": ["success criteria", "acceptance criteria", "kpis",
                         "service levels", "sla"],
}


def _heuristic_extract(text: str) -> dict:
    """Deterministic fallback: pull sections that follow known headings."""
    import re
    out = {k: "" for k in _KB_FIELDS}
    lines = text.splitlines()
    # Index every line that looks like a heading for one of our fields.
    hits = []  # (line_no, field)
    for i, ln in enumerate(lines):
        bare = re.sub(r"^[\d\.\)\s#*·-]+", "", ln).strip().lower().rstrip(":")
        if not bare or len(bare) > 60:
            continue
        for field, aliases in _HEADING_MAP.items():
            if any(bare == a or bare.startswith(a) for a in aliases):
                hits.append((i, field))
                break
    hits.sort()
    for n, (i, field) in enumerate(hits):
        end = hits[n + 1][0] if n + 1 < len(hits) else min(len(lines), i + 40)
        body = "\n".join(l.strip() for l in lines[i + 1:end] if l.strip())
        if body and not out[field]:
            out[field] = body[:1500]
    return out


def extract_project_fields(text: str, doc_type: str = "RFP") -> dict:
    """Extract charter-style project fields from a document's text.

    Uses the Anthropic API when configured (rich, cross-referenced
    extraction); otherwise falls back to deterministic heading-based parsing
    so the feature still works fully offline. Returns a dict with the keys in
    _KB_FIELDS plus 'milestones' (list of str) and 'risks' (list of str).
    """
    snippet = text[:24000]  # keep the prompt bounded
    prompt = (
        f"You are a senior IT infrastructure PM. Below is the text of a {doc_type}. "
        "Extract the following as strict JSON with EXACTLY these keys and no "
        "other text, no markdown fences: "
        '{"name": "short project name", "customer": "", "project_type": "", '
        '"region": "", "business_case": "", "scope": "", "objectives": "", '
        '"deliverables": "", "assumptions": "", "constraints": "", '
        '"success_criteria": "", "milestones": ["..."], "risks": ["..."]}. '
        "Each text field: concise (max ~120 words), factual, drawn only from the "
        "document; empty string if absent. milestones: up to 6 key phases/dates. "
        "risks: up to 6 delivery risks stated or implied.\n\nDOCUMENT:\n" + snippet
    )
    raw = _call_anthropic(prompt, system="Return strict JSON only.")
    if raw:
        import json, re
        raw = re.sub(r"^```(json)?|```$", "", raw.strip(), flags=re.M).strip()
        try:
            data = json.loads(raw)
            out = {k: str(data.get(k, "") or "") for k in _KB_FIELDS}
            out["milestones"] = [str(x) for x in data.get("milestones", [])][:6]
            out["risks"] = [str(x) for x in data.get("risks", [])][:6]
            out["_engine"] = "AI"
            return out
        except Exception:
            pass  # fall through to heuristic
    out = _heuristic_extract(text)
    out["milestones"], out["risks"], out["_engine"] = [], [], "heuristic"
    return out
