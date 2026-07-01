"""Data Management: full add / edit / delete + import / export for every entity.

A single page that turns the toolkit from a viewer into an editable system of
record. Driven entirely by the generic engine in core.crud, so it covers every
model with no per-entity code.
"""
import streamlit as st

from core import models as m
from core.crud import editable_grid, import_export_panel
from modules.common import list_projects, section_title

# Friendly name -> (model, scope_fk). scope_fk=None means a global table.
GLOBAL_ENTITIES = {
    "Projects": (m.Project, None),
    "Resources": (m.Resource, None),
    "Vendors": (m.Vendor, None),
    "Users": (m.User, None),
}

PROJECT_ENTITIES = {
    "WBS Tasks": (m.WBSTask, "project_id"),
    "Milestones": (m.Milestone, "project_id"),
    "Stakeholders": (m.Stakeholder, "project_id"),
    "RAID Items": (m.RaidItem, "project_id"),
    "Budget Lines": (m.BudgetLine, "project_id"),
    "Change Requests": (m.ChangeRequest, "project_id"),
    "Purchase Orders": (m.PurchaseOrder, "project_id"),
    "Meetings": (m.Meeting, "project_id"),
    "Migration Sites": (m.MigrationSite, "project_id"),
    "Quality Items": (m.QualityItem, "project_id"),
    "Compliance Items": (m.ComplianceItem, "project_id"),
    "Lessons Learned": (m.LessonLearned, "project_id"),
    "Allocations": (m.Allocation, "project_id"),
    "Timesheets": (m.Timesheet, "project_id"),
}


def render():
    section_title("Data Management",
                  "Add, edit, delete and bulk-import records across the toolkit")

    scope = st.radio("Scope", ["Global tables", "Project-scoped tables"],
                     horizontal=True, key="dm_scope")

    if scope == "Global tables":
        name = st.selectbox("Entity", list(GLOBAL_ENTITIES.keys()), key="dm_global")
        model, fk = GLOBAL_ENTITIES[name]
        st.caption(f"Editing **{name}** — {model.__tablename__}")
        import_export_panel(model, key=f"io_{name}")
        editable_grid(model, key=f"grid_{name}")
    else:
        projects = list_projects()
        if not projects:
            st.warning("No projects yet. Seed sample data from Settings, or add a "
                       "project under Global tables → Projects first.")
            return
        labels = {f"{p.code} — {p.name}": p.id for p in projects}
        pcol, ecol = st.columns(2)
        proj_label = pcol.selectbox("Project", list(labels.keys()), key="dm_proj")
        name = ecol.selectbox("Entity", list(PROJECT_ENTITIES.keys()), key="dm_pe")
        pid = labels[proj_label]
        model, fk = PROJECT_ENTITIES[name]
        st.caption(f"Editing **{name}** for **{proj_label}**")
        import_export_panel(model, scope_fk=fk, scope_id=pid, key=f"io_{name}_{pid}")
        editable_grid(model, scope_fk=fk, scope_id=pid, key=f"grid_{name}_{pid}")
