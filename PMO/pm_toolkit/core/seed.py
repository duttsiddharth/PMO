"""Seed the database with realistic sample IT infrastructure projects.

Run directly:  python -m core.seed     (from the pm_toolkit directory)
or via the app's Settings page. Idempotent: it resets the schema each run.
"""
import random
from datetime import date, timedelta

from core.database import reset_db, Session
from core import models as m

random.seed(42)
COMPLIANCE_ARTIFACTS = [
    "Project Charter", "Scope Document", "PMP", "Schedule", "Budget",
    "RAID Log", "Change Log", "Communication Plan", "Quality Plan",
    "Acceptance Documents", "Lessons Learned", "Closure Report",
]


def _d(days_from_today: int) -> date:
    return date.today() + timedelta(days=days_from_today)


def seed() -> None:
    reset_db()
    s = Session()

    # --- Users -----------------------------------------------------------
    users = [
        m.User(name="Siddharth Dutt", email="pm@sdadvisory.io", role="PM"),
        m.User(name="Admin", email="admin@sdadvisory.io", role="Admin"),
        m.User(name="A. Sharma", email="asharma@client.com", role="Team Member"),
        m.User(name="Client Sponsor", email="sponsor@royalfrs.gov", role="Customer"),
    ]
    s.add_all(users)

    # --- Shared resources -----------------------------------------------
    resources = [
        m.Resource(name="N. Rao", role="Network Architect", skills="WAN,SD-WAN,BGP,MPLS", cost_rate=85, capacity_hours=40),
        m.Resource(name="P. Mehta", role="Security Engineer", skills="Firewall,Zscaler,Palo Alto", cost_rate=80, capacity_hours=40),
        m.Resource(name="J. Lee", role="Cloud Engineer", skills="AWS,Azure,Migration", cost_rate=90, capacity_hours=40),
        m.Resource(name="R. Khan", role="UC Consultant", skills="Teams,SIP,Avaya", cost_rate=75, capacity_hours=40),
        m.Resource(name="S. Iyer", role="Project Coordinator", skills="Scheduling,Reporting", cost_rate=55, capacity_hours=40),
    ]
    s.add_all(resources)
    s.flush()

    vendors = [
        m.Vendor(name="Cisco Systems", category="Hardware", contact="acct@cisco.com", sla_target="NBD hardware", sla_status="On Track"),
        m.Vendor(name="Palo Alto Networks", category="Security", contact="sales@paloalto.com", sla_target="4h critical", sla_status="On Track"),
        m.Vendor(name="Local ISP", category="Connectivity", contact="noc@isp.com", sla_target="99.9% uptime", sla_status="At Risk"),
    ]
    s.add_all(vendors)
    s.flush()

    projects_spec = [
        dict(code="PRJ-WAN-001", name="Global WAN / SD-WAN Refresh", customer="Royal FRS",
             project_type="SD-WAN", region="EMEA", status="Execution", health="Amber",
             budget=1_250_000, pct=58),
        dict(code="PRJ-DC-002", name="Data Center to Cloud Migration", customer="Acme Manufacturing",
             project_type="Cloud Migration", region="APAC", status="Execution", health="Green",
             budget=920_000, pct=41),
        dict(code="PRJ-UC-003", name="Unified Communications Rollout", customer="Northwind Bank",
             project_type="Unified Communications", region="Americas", status="Planning", health="Green",
             budget=480_000, pct=18),
    ]

    for spec in projects_spec:
        p = m.Project(
            code=spec["code"], name=spec["name"], customer=spec["customer"],
            project_type=spec["project_type"], region=spec["region"],
            pm_name="Siddharth Dutt", status=spec["status"], health=spec["health"],
            start_date=_d(-120), end_date=_d(150), budget=spec["budget"],
            percent_complete=spec["pct"],
            business_case=f"Modernise {spec['project_type']} estate to reduce opex and improve resilience.",
            scope=f"Design, build, migrate and operate the {spec['project_type']} solution across all in-scope sites.",
            objectives="Reduce MTTR, improve SLA adherence, lower TCO by 20%.",
            deliverables="HLD, LLD, migration runbooks, as-built docs, operational handover.",
            assumptions="Sites accessible during change windows; vendor lead times honoured.",
            constraints="Fixed go-live; frozen change window over quarter-end.",
            success_criteria="Zero P1 incidents post-cutover; UAT sign-off; SLA >= 99.8%.",
        )
        s.add(p)
        s.flush()

        # Stakeholders + RACI
        s.add_all([
            m.Stakeholder(project_id=p.id, name="Programme Sponsor", org=p.customer, role="Sponsor",
                          influence="High", interest="High", raci="A", contact="sponsor@client.com"),
            m.Stakeholder(project_id=p.id, name="IT Director", org=p.customer, role="Decision Maker",
                          influence="High", interest="Medium", raci="C", contact="itdir@client.com"),
            m.Stakeholder(project_id=p.id, name="Network Lead", org="SD Advisory", role="Delivery",
                          influence="Medium", interest="High", raci="R", contact="net@sdadvisory.io"),
        ])

        # WBS tasks with EVM-relevant numbers
        phases = ["Initiation", "Design", "Procurement", "Build", "Migration", "Closure"]
        per_phase_cost = spec["budget"] / len(phases)
        for i, phase in enumerate(phases):
            pct = max(0, min(100, spec["pct"] + random.randint(-25, 35) - i * 5))
            planned = round(per_phase_cost, 0)
            actual = round(planned * (pct / 100.0) * random.uniform(0.92, 1.18), 0)
            s.add(m.WBSTask(
                project_id=p.id, wbs_code=f"{i+1}.0", name=f"{phase} workstream",
                phase=phase, owner=random.choice([r.name for r in resources]),
                start_date=_d(-110 + i * 25), end_date=_d(-110 + (i + 1) * 25),
                depends_on=f"{i}.0" if i else "", is_critical=(i in (1, 3, 4)),
                planned_cost=planned, actual_cost=actual, percent_complete=pct,
                status="Complete" if pct >= 100 else ("In Progress" if pct > 0 else "Not Started"),
            ))

        # Milestones
        s.add_all([
            m.Milestone(project_id=p.id, name="Design Approved", due_date=_d(-40), status="Done"),
            m.Milestone(project_id=p.id, name="First Site Live", due_date=_d(10), status="Pending"),
            m.Milestone(project_id=p.id, name="Final Cutover", due_date=_d(120), status="Pending"),
        ])

        # Allocations + timesheets
        for r in resources[:4]:
            s.add(m.Allocation(project_id=p.id, resource_id=r.id, allocation_pct=random.choice([25, 50, 75, 100])))
            for w in range(4):
                planned_h = 40
                s.add(m.Timesheet(project_id=p.id, resource_id=r.id, week_ending=_d(-7 * (4 - w)),
                                  planned_hours=planned_h, actual_hours=planned_h * random.uniform(0.8, 1.15)))

        # Budget lines by month/category
        months = [(_d(-90 + 30 * k)).strftime("%Y-%m") for k in range(5)]
        for cat in ["Hardware", "Software", "Travel", "Services", "Labour"]:
            for mth in months:
                planned = round(spec["budget"] / 25, 0)
                s.add(m.BudgetLine(project_id=p.id, category=cat, description=f"{cat} spend",
                                   planned=planned, actual=round(planned * random.uniform(0.7, 1.2), 0),
                                   forecast=round(planned * random.uniform(0.95, 1.1), 0), month=mth))

        # POs
        for v in vendors:
            s.add(m.PurchaseOrder(project_id=p.id, vendor_id=v.id, po_number=f"PO-{p.id}{v.id:02d}",
                                  description=f"{v.category} supply", amount=round(spec['budget'] / 8, 0),
                                  status=random.choice(["Open", "Delivered", "Invoiced"]),
                                  delivery_status=random.choice(["Pending", "Delivered"]),
                                  invoice_status=random.choice(["Pending", "Paid"])))

        # RAID
        s.add_all([
            m.RaidItem(project_id=p.id, category="Risk", title="ISP circuit lead time slip",
                       owner="N. Rao", severity="High", probability=4, impact=4,
                       mitigation="Order circuits early; arrange temporary 4G failover.",
                       due_date=_d(20), status="Open"),
            m.RaidItem(project_id=p.id, category="Risk", title="Change window contention",
                       owner="S. Iyer", severity="Medium", probability=3, impact=3,
                       mitigation="Lock change calendar with CAB.", due_date=_d(15), status="Open"),
            m.RaidItem(project_id=p.id, category="Assumption", title="Sites accessible in window",
                       owner="PM", severity="Low", probability=2, impact=2, status="Open"),
            m.RaidItem(project_id=p.id, category="Issue", title="Firmware incompatibility on legacy switches",
                       owner="P. Mehta", severity="High", probability=5, impact=4,
                       mitigation="Stage firmware upgrade ahead of cutover.", due_date=_d(5), status="Open"),
            m.RaidItem(project_id=p.id, category="Dependency", title="Customer DNS changes",
                       owner="Client", severity="Medium", probability=3, impact=4,
                       mitigation="Joint runbook with customer network team.", due_date=_d(8), status="Open"),
        ])

        # Change requests
        s.add_all([
            m.ChangeRequest(project_id=p.id, cr_number=f"CR-{p.id}01",
                            description="Add 3 additional remote sites to scope",
                            justification="Customer acquisition added new offices.",
                            scope_impact="3 sites", cost_impact=85_000, schedule_impact_days=21,
                            raised_by="Sponsor", approver="IT Director", status="Under Review"),
            m.ChangeRequest(project_id=p.id, cr_number=f"CR-{p.id}02",
                            description="Upgrade firewalls to next-gen models",
                            justification="Security posture improvement.",
                            scope_impact="Firewall tier", cost_impact=40_000, schedule_impact_days=7,
                            raised_by="Network Lead", approver="IT Director", status="Approved"),
        ])

        # Meetings + actions
        mtg = m.Meeting(project_id=p.id, title="Weekly Status Call", meeting_date=_d(-3),
                        attendees="PM, Sponsor, Network Lead", agenda="Progress, risks, decisions",
                        minutes="Reviewed cutover plan; ISP risk discussed.",
                        decisions="Proceed with phased cutover.")
        mtg.action_items = [
            m.ActionItem(description="Confirm ISP circuit dates", owner="N. Rao", due_date=_d(4), status="Open"),
            m.ActionItem(description="Finalise rollback runbook", owner="P. Mehta", due_date=_d(6), status="Open"),
        ]
        s.add(mtg)

        # Migration sites
        for k in range(4):
            s.add(m.MigrationSite(project_id=p.id, migration_type=spec["project_type"].split()[0],
                                  site=f"Site-{k+1:02d}", scheduled_date=_d(-10 + k * 10),
                                  status=random.choice(["Planned", "In Progress", "Migrated"]),
                                  rollback_plan="Restore prior config from backup; revert routing.",
                                  acceptance=random.choice(["Pending", "Accepted"])))

        # Quality
        s.add_all([
            m.QualityItem(project_id=p.id, item_type="Audit", finding="Documentation lagging build progress",
                          corrective_action="Catch-up doc sprint", preventive_action="Doc-as-you-build policy",
                          owner="S. Iyer", status="Open"),
            m.QualityItem(project_id=p.id, item_type="NCR", finding="One site cabling non-conformance",
                          corrective_action="Re-terminate to standard", preventive_action="QA checklist at install",
                          owner="N. Rao", status="Closed"),
        ])

        # Compliance
        for j, art in enumerate(COMPLIANCE_ARTIFACTS):
            done = j < (8 if spec["status"] == "Execution" else 5)
            s.add(m.ComplianceItem(project_id=p.id, artifact=art, complete=done))

        # Lessons
        s.add_all([
            m.LessonLearned(project_id=p.id, category="Success", summary="Early vendor engagement cut lead times"),
            m.LessonLearned(project_id=p.id, category="Challenge", summary="Change window contention with customer ops"),
            m.LessonLearned(project_id=p.id, category="Recommendation", summary="Pre-stage firmware before cutover"),
        ])

    s.commit()
    s.close()
    print("Seeded sample data: 3 projects with full lifecycle records.")


if __name__ == "__main__":
    seed()
