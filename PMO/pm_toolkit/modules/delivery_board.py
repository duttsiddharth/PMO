"""Delivery Board: portfolio delivery rail + kanban task board with
role-based edit permissions.

Ported from the SD Delivery OS prototype. Adds three capabilities on top of
the existing toolkit:

1. Delivery rail — a visual lifecycle tracker (Presales → Planning →
   Execution → Closure) rendered per project, portfolio-wide and in detail.
2. Kanban task board — WBS tasks grouped by status with one-click advance
   (Not Started → In Progress → Blocked → Complete). "Blocked" is a plain
   string value on WBSTask.status, so no schema migration is needed.
3. Edit-level permissions — config.ROLE_PERMISSIONS gates *actions* (not just
   page visibility): Vendors may only advance their own tasks, Sponsors and
   Customers are read-only, Admin/PM have full control.
"""
from __future__ import annotations

import streamlit as st

import config
from core import models as m
from modules.common import get_session, list_projects, project_evm, section_title
from modules.theme import RAG, rag_pill

KANBAN_COLS = ["Not Started", "In Progress", "Blocked", "Complete"]


# --------------------------------------------------------------------------
# Permissions
# --------------------------------------------------------------------------
def _role() -> str:
    return st.session_state.get("role", "Customer")


def can(action: str) -> bool:
    """True if the current role may perform *action*.

    Actions: edit_tasks, edit_own_tasks, edit_stage, edit_rag, view_finance.
    Falls back to read-only when the role or action is unknown.
    """
    perms = getattr(config, "ROLE_PERMISSIONS", {})
    return action in perms.get(_role(), [])


# --------------------------------------------------------------------------
# Delivery rail
# --------------------------------------------------------------------------
def _stage_index(status: str) -> int:
    stages = getattr(config, "STAGES", ["Presales", "Planning", "Execution", "Closure"])
    return stages.index(status) if status in stages else 0


def rail_html(status: str) -> str:
    """Compact HTML delivery rail for the given project status."""
    stages = getattr(config, "STAGES", ["Presales", "Planning", "Execution", "Closure"])
    now = _stage_index(status)
    segs = []
    for i, s in enumerate(stages):
        if i < now:
            bar, txt = "#F97316", "#94A3B8"
        elif i == now:
            bar, txt = "linear-gradient(90deg,#F97316,#FDBA74)", "#F97316"
        else:
            bar, txt = "#334155", "#64748B"
        glow = "box-shadow:0 0 10px rgba(249,115,22,.55);" if i == now else ""
        segs.append(
            f"<div style='flex:1'>"
            f"<div style='height:6px;border-radius:99px;background:{bar};{glow}'></div>"
            f"<div style='font-size:.68rem;text-align:center;margin-top:3px;"
            f"letter-spacing:.06em;color:{txt}'>{s}</div></div>"
        )
    return ("<div style='display:flex;gap:6px;align-items:flex-start;"
            "margin:.35rem 0 .5rem'>" + "".join(segs) + "</div>")


# --------------------------------------------------------------------------
# Kanban board
# --------------------------------------------------------------------------
def _advance(task_id: int):
    s = get_session()
    t = s.get(m.WBSTask, task_id)
    if t is None:
        return
    nxt = KANBAN_COLS[(KANBAN_COLS.index(t.status) + 1) % len(KANBAN_COLS)] \
        if t.status in KANBAN_COLS else "In Progress"
    t.status = nxt
    if nxt == "Complete":
        t.percent_complete = 100.0
    elif nxt == "In Progress" and t.percent_complete in (0.0, 100.0):
        t.percent_complete = 25.0
    s.commit()


def _may_move(task) -> bool:
    if can("edit_tasks"):
        return True
    if can("edit_own_tasks"):
        me = st.session_state.get("actor_name", "").strip().lower()
        return bool(me) and me in (task.owner or "").lower()
    return False


def _kanban(project):
    tasks = sorted(project.tasks, key=lambda t: (t.wbs_code or ""))
    if can("edit_own_tasks") and not can("edit_tasks"):
        owners = sorted({t.owner for t in tasks if t.owner})
        st.selectbox("I am (vendor/team identity — you can move only your own tasks)",
                     [""] + owners, key="actor_name")

    cols = st.columns(len(KANBAN_COLS), gap="small")
    for col, status in zip(cols, KANBAN_COLS):
        bucket = [t for t in tasks if (t.status if t.status in KANBAN_COLS else "Not Started") == status]
        accent = {"Blocked": "#DC2626", "Complete": "#16A34A",
                  "In Progress": "#F97316"}.get(status, "#64748B")
        col.markdown(
            f"<div style='font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;"
            f"color:{accent};margin-bottom:.3rem'>{status} · {len(bucket)}</div>",
            unsafe_allow_html=True)
        for t in bucket:
            with col.container(border=True):
                crit = " 🔺" if t.is_critical else ""
                st.markdown(f"**{t.wbs_code or ''}** {t.name}{crit}")
                st.caption(f"{t.owner or '—'} · {t.percent_complete:.0f}%")
                if status != "Complete" and _may_move(t):
                    st.button("Advance →", key=f"adv_{t.id}",
                              on_click=_advance, args=(t.id,),
                              use_container_width=True)


# --------------------------------------------------------------------------
# Views
# --------------------------------------------------------------------------
def _portfolio():
    projects = list_projects()
    if not projects:
        st.info("No projects yet. Seed sample data from the Settings page.")
        return

    for p in projects:
        with st.container(border=True):
            head, burn, btn = st.columns([5, 2, 1.2])
            dot = RAG.get(p.health, "#64748B")
            head.markdown(
                f"<span style='display:inline-block;width:10px;height:10px;border-radius:99px;"
                f"background:{dot};box-shadow:0 0 8px {dot};margin-right:8px'></span>"
                f"<b>{p.name}</b> &nbsp;<span style='color:#64748B;font-size:.8rem'>"
                f"{p.code} · {p.customer}</span>", unsafe_allow_html=True)
            if can("view_finance"):
                e = project_evm(p)
                burn.caption(f"AC {e.ac:,.0f} / BAC {e.bac:,.0f}")
            btn.button("Open", key=f"open_{p.id}", use_container_width=True,
                       on_click=lambda pid=p.id: st.session_state.update(db_project=pid))
            st.markdown(rail_html(p.status), unsafe_allow_html=True)


def _detail(pid: int):
    s = get_session()
    p = s.get(m.Project, pid)
    if p is None:
        st.session_state.pop("db_project", None)
        st.rerun()
        return

    st.button("← Portfolio", on_click=lambda: st.session_state.pop("db_project", None))

    c1, c2, c3 = st.columns([5, 1.4, 1.4])
    c1.markdown(f"### {p.name} &nbsp;{rag_pill(p.health)}", unsafe_allow_html=True)

    stages = getattr(config, "STAGES", ["Presales", "Planning", "Execution", "Closure"])
    if can("edit_stage"):
        new_stage = c2.selectbox("Stage", stages, index=_stage_index(p.status),
                                 label_visibility="collapsed")
        if new_stage != p.status:
            p.status = new_stage
            s.commit()
            st.rerun()
    if can("edit_rag"):
        new_rag = c3.selectbox("RAG", list(RAG), index=list(RAG).index(p.health)
                               if p.health in RAG else 0, label_visibility="collapsed")
        if new_rag != p.health:
            p.health = new_rag
            s.commit()
            st.rerun()

    st.markdown(rail_html(p.status), unsafe_allow_html=True)

    blocked = sum(1 for t in p.tasks if t.status == "Blocked")
    if blocked:
        st.warning(f"{blocked} task(s) currently blocked — review before the next stage gate.")

    _kanban(p)
    if not can("edit_tasks") and not can("edit_own_tasks"):
        st.caption(f"Read-only view for the {_role()} role.")


def render():
    section_title("Delivery Board",
                  "Lifecycle rail and kanban across the portfolio — role-aware editing")
    pid = st.session_state.get("db_project")
    if pid:
        _detail(pid)
    else:
        _portfolio()
