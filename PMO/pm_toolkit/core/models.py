"""SQLAlchemy ORM models for the IT Infrastructure PM Toolkit.

The schema is intentionally broad: a single Project owns the full lifecycle of
related records (charter, WBS, RAID, budget, change, vendors, meetings,
migration, quality, compliance, lessons, acceptance). RAID items share one
table differentiated by `category` so the four RAID tabs are simple filters.
"""
from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# --------------------------------------------------------------------------
# Identity / access
# --------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(180), unique=True, nullable=False)
    role = Column(String(40), nullable=False, default="Team Member")
    active = Column(Boolean, default=True)


# --------------------------------------------------------------------------
# Project + initiation
# --------------------------------------------------------------------------
class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    code = Column(String(40), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    customer = Column(String(160))
    project_type = Column(String(80))
    region = Column(String(80))
    pm_name = Column(String(120))
    status = Column(String(40), default="Planning")          # Presales/Planning/Execution/Closure
    health = Column(String(10), default="Green")             # Green/Amber/Red (RAG)
    start_date = Column(Date)
    end_date = Column(Date)
    budget = Column(Float, default=0.0)                       # Budget at Completion (BAC)
    percent_complete = Column(Float, default=0.0)

    # Charter / business case (free text fields)
    business_case = Column(Text, default="")
    scope = Column(Text, default="")
    objectives = Column(Text, default="")
    deliverables = Column(Text, default="")
    assumptions = Column(Text, default="")
    constraints = Column(Text, default="")
    success_criteria = Column(Text, default="")

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    stakeholders = relationship("Stakeholder", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("WBSTask", back_populates="project", cascade="all, delete-orphan")
    milestones = relationship("Milestone", back_populates="project", cascade="all, delete-orphan")
    raid = relationship("RaidItem", back_populates="project", cascade="all, delete-orphan")
    budget_lines = relationship("BudgetLine", back_populates="project", cascade="all, delete-orphan")
    changes = relationship("ChangeRequest", back_populates="project", cascade="all, delete-orphan")
    meetings = relationship("Meeting", back_populates="project", cascade="all, delete-orphan")
    migrations = relationship("MigrationSite", back_populates="project", cascade="all, delete-orphan")
    quality = relationship("QualityItem", back_populates="project", cascade="all, delete-orphan")
    compliance = relationship("ComplianceItem", back_populates="project", cascade="all, delete-orphan")
    lessons = relationship("LessonLearned", back_populates="project", cascade="all, delete-orphan")
    allocations = relationship("Allocation", back_populates="project", cascade="all, delete-orphan")


class Stakeholder(Base):
    __tablename__ = "stakeholders"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    name = Column(String(120))
    org = Column(String(160))
    role = Column(String(120))
    influence = Column(String(20), default="Medium")     # Low/Medium/High
    interest = Column(String(20), default="Medium")
    raci = Column(String(20), default="C")               # R/A/C/I
    contact = Column(String(160))
    project = relationship("Project", back_populates="stakeholders")


# --------------------------------------------------------------------------
# Planning: WBS / schedule / milestones
# --------------------------------------------------------------------------
class WBSTask(Base):
    __tablename__ = "wbs_tasks"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    wbs_code = Column(String(40))
    name = Column(String(200))
    phase = Column(String(80))
    owner = Column(String(120))
    start_date = Column(Date)
    end_date = Column(Date)
    depends_on = Column(String(80), default="")          # comma-sep wbs_codes
    is_critical = Column(Boolean, default=False)
    planned_cost = Column(Float, default=0.0)            # planned value contribution
    actual_cost = Column(Float, default=0.0)
    percent_complete = Column(Float, default=0.0)
    status = Column(String(40), default="Not Started")
    project = relationship("Project", back_populates="tasks")


class Milestone(Base):
    __tablename__ = "milestones"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    name = Column(String(200))
    due_date = Column(Date)
    status = Column(String(40), default="Pending")
    project = relationship("Project", back_populates="milestones")


# --------------------------------------------------------------------------
# Resources
# --------------------------------------------------------------------------
class Resource(Base):
    __tablename__ = "resources"
    id = Column(Integer, primary_key=True)
    name = Column(String(120))
    role = Column(String(120))
    skills = Column(String(300))                         # comma-sep
    cost_rate = Column(Float, default=0.0)               # per hour
    capacity_hours = Column(Float, default=40.0)         # weekly
    allocations = relationship("Allocation", back_populates="resource", cascade="all, delete-orphan")
    timesheets = relationship("Timesheet", back_populates="resource", cascade="all, delete-orphan")


class Allocation(Base):
    __tablename__ = "allocations"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    resource_id = Column(Integer, ForeignKey("resources.id"))
    allocation_pct = Column(Float, default=0.0)
    project = relationship("Project", back_populates="allocations")
    resource = relationship("Resource", back_populates="allocations")


class Timesheet(Base):
    __tablename__ = "timesheets"
    id = Column(Integer, primary_key=True)
    resource_id = Column(Integer, ForeignKey("resources.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    week_ending = Column(Date)
    planned_hours = Column(Float, default=0.0)
    actual_hours = Column(Float, default=0.0)
    resource = relationship("Resource", back_populates="timesheets")


# --------------------------------------------------------------------------
# Budget / procurement
# --------------------------------------------------------------------------
class BudgetLine(Base):
    __tablename__ = "budget_lines"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    category = Column(String(80))                        # Hardware/Software/Travel/Services/Labour
    description = Column(String(240))
    planned = Column(Float, default=0.0)
    actual = Column(Float, default=0.0)
    forecast = Column(Float, default=0.0)
    month = Column(String(7))                            # YYYY-MM for monthly-spend charts
    project = relationship("Project", back_populates="budget_lines")


class Vendor(Base):
    __tablename__ = "vendors"
    id = Column(Integer, primary_key=True)
    name = Column(String(160))
    category = Column(String(120))
    contact = Column(String(160))
    sla_target = Column(String(120))
    sla_status = Column(String(40), default="On Track")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    vendor_id = Column(Integer, ForeignKey("vendors.id"))
    po_number = Column(String(60))
    description = Column(String(240))
    amount = Column(Float, default=0.0)
    status = Column(String(40), default="Open")          # Open/Delivered/Invoiced/Closed
    delivery_status = Column(String(40), default="Pending")
    invoice_status = Column(String(40), default="Pending")


# --------------------------------------------------------------------------
# RAID (Risks / Assumptions / Issues / Dependencies)
# --------------------------------------------------------------------------
class RaidItem(Base):
    __tablename__ = "raid_items"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    category = Column(String(20))                        # Risk/Assumption/Issue/Dependency
    title = Column(String(240))
    description = Column(Text, default="")
    owner = Column(String(120))
    severity = Column(String(20), default="Medium")      # Low/Medium/High/Critical
    probability = Column(Integer, default=3)             # 1..5 (risks)
    impact = Column(Integer, default=3)                  # 1..5 (risks)
    mitigation = Column(Text, default="")
    due_date = Column(Date)
    status = Column(String(30), default="Open")
    project = relationship("Project", back_populates="raid")

    @property
    def risk_score(self) -> int:
        return int(self.probability or 0) * int(self.impact or 0)


# --------------------------------------------------------------------------
# Change management
# --------------------------------------------------------------------------
class ChangeRequest(Base):
    __tablename__ = "change_requests"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    cr_number = Column(String(40))
    description = Column(Text)
    justification = Column(Text, default="")
    scope_impact = Column(String(240), default="")
    cost_impact = Column(Float, default=0.0)
    schedule_impact_days = Column(Integer, default=0)
    raised_by = Column(String(120))
    approver = Column(String(120))
    status = Column(String(30), default="Submitted")     # Submitted/Under Review/Approved/Rejected
    raised_on = Column(Date, default=date.today)
    project = relationship("Project", back_populates="changes")


# --------------------------------------------------------------------------
# Meetings
# --------------------------------------------------------------------------
class Meeting(Base):
    __tablename__ = "meetings"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    title = Column(String(200))
    meeting_date = Column(Date)
    attendees = Column(Text, default="")
    agenda = Column(Text, default="")
    minutes = Column(Text, default="")
    decisions = Column(Text, default="")
    project = relationship("Project", back_populates="meetings")
    action_items = relationship("ActionItem", back_populates="meeting", cascade="all, delete-orphan")


class ActionItem(Base):
    __tablename__ = "action_items"
    id = Column(Integer, primary_key=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    description = Column(String(300))
    owner = Column(String(120))
    due_date = Column(Date)
    status = Column(String(30), default="Open")
    meeting = relationship("Meeting", back_populates="action_items")


# --------------------------------------------------------------------------
# Migration tracker
# --------------------------------------------------------------------------
class MigrationSite(Base):
    __tablename__ = "migration_sites"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    migration_type = Column(String(60))                  # WAN/LAN/DC/Cloud/Firewall/SD-WAN
    site = Column(String(160))
    scheduled_date = Column(Date)
    status = Column(String(40), default="Planned")       # Planned/In Progress/Migrated/Rolled Back
    rollback_plan = Column(Text, default="")
    acceptance = Column(String(40), default="Pending")
    project = relationship("Project", back_populates="migrations")


# --------------------------------------------------------------------------
# Quality
# --------------------------------------------------------------------------
class QualityItem(Base):
    __tablename__ = "quality_items"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    item_type = Column(String(40))                       # Audit/NCR/CAPA/Acceptance
    finding = Column(Text)
    corrective_action = Column(Text, default="")
    preventive_action = Column(Text, default="")
    owner = Column(String(120))
    status = Column(String(30), default="Open")
    project = relationship("Project", back_populates="quality")


# --------------------------------------------------------------------------
# PMO compliance
# --------------------------------------------------------------------------
class ComplianceItem(Base):
    __tablename__ = "compliance_items"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    artifact = Column(String(120))                       # Charter/Scope/PMP/...
    complete = Column(Boolean, default=False)
    project = relationship("Project", back_populates="compliance")


# --------------------------------------------------------------------------
# Lessons learned
# --------------------------------------------------------------------------
class LessonLearned(Base):
    __tablename__ = "lessons_learned"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    category = Column(String(40))                        # Success/Challenge/Recommendation/Best Practice
    summary = Column(Text)
    detail = Column(Text, default="")
    project = relationship("Project", back_populates="lessons")


# --------------------------------------------------------------------------
# Portfolio snapshots (EVM trend history)
# --------------------------------------------------------------------------
class PortfolioSnapshot(Base):
    """One row per project per snapshot date. Written by core.snapshots.

    Purely additive table: created automatically by Base.metadata.create_all,
    so existing SQLite/Postgres databases pick it up with no migration.
    """
    __tablename__ = "portfolio_snapshots"
    id = Column(Integer, primary_key=True)
    snap_date = Column(Date, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"))
    project_code = Column(String(40))
    health = Column(String(10))
    status = Column(String(40))
    spi = Column(Float, default=0.0)
    cpi = Column(Float, default=0.0)
    percent_complete = Column(Float, default=0.0)
    ac = Column(Float, default=0.0)
    bac = Column(Float, default=0.0)
    open_risks = Column(Integer, default=0)
    open_issues = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
