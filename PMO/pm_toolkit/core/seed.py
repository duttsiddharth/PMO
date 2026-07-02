"""Seed the database with a realistic Meridian Group delivery programme.

Content is grounded in the "Global WAN, LAN, UC&C and Security Services" RFP
(customer: Meridian Group (fictional); advisor: Advisory Partner Co (fictional)). Four in-flight delivery
projects model the four service towers, with RFP-accurate scope, in-scope
countries, site types, SLA tiers, licence volumes and risks.

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

# 12 in-scope countries from the RFP (WAN/LAN/UC&C/Security).
COUNTRIES = [
    ("Netherlands (HQ)", "E"), ("Belgium", "E"), ("France", "E"),
    ("Germany", "E"), ("Italy", "B"), ("Romania", "B"),
    ("United Kingdom", "E"), ("China", "Q"), ("Hong Kong", "B+"),
    ("Indonesia", "B"), ("Malaysia", "B"), ("Singapore (DR)", "F"),
]


def _d(days_from_today: int) -> date:
    return date.today() + timedelta(days=days_from_today)


def seed() -> None:
    reset_db()
    s = Session()

    # --- Users -----------------------------------------------------------
    s.add_all([
        m.User(name="Siddharth Dutt", email="pm@sdadvisory.io", role="PM"),
        m.User(name="Admin", email="admin@sdadvisory.io", role="Admin"),
        m.User(name="Client Sponsor", email="sponsor@meridiangroup.example", role="Customer"),
        m.User(name="Advisor PMO Lead", email="pmo@advisorypartner.example", role="Team Member"),
    ])

    # --- Shared resource pool -------------------------------------------
    resources = [
        m.Resource(name="N. Rao", role="WAN / Network Architect", skills="MPLS,SD-WAN,BGP,WAAS,QoS", cost_rate=95, capacity_hours=40),
        m.Resource(name="P. Mehta", role="Security / SOC Lead", skills="SIEM,IPS,Segmentation,Vuln Mgmt,Threat Intel", cost_rate=98, capacity_hours=40),
        m.Resource(name="R. Khan", role="UC&C Consultant", skills="Enterprise UC,Enterprise Voice,SIP,Conferencing", cost_rate=88, capacity_hours=40),
        m.Resource(name="L. Novak", role="LAN / WLAN Engineer", skills="Enterprise LAN,WLAN,NAC,802.1X", cost_rate=82, capacity_hours=40),
        m.Resource(name="M. Silva", role="Transition Manager", skills="Transition,Service Mgmt,ITIL", cost_rate=90, capacity_hours=40),
        m.Resource(name="S. Iyer", role="PMO Coordinator", skills="Scheduling,Reporting,RAID", cost_rate=60, capacity_hours=40),
    ]
    s.add_all(resources)
    s.flush()

    # --- Vendors ---------------------------------------------------------
    vendors = [
        m.Vendor(name="Global MPLS Carrier", category="Connectivity", contact="service@carrier.example", sla_target="99.90% availability", sla_status="On Track"),
        m.Vendor(name="Network Hardware OEM", category="Hardware", contact="accounts@hw-oem.example", sla_target="NBD hardware / WAN optimisation", sla_status="On Track"),
        m.Vendor(name="UC&C Platform Vendor", category="UC&C Licensing", contact="licensing@uc-vendor.example", sla_target="99.9% cloud", sla_status="On Track"),
        m.Vendor(name="Managed SOC / SIEM Provider", category="Security", contact="soc@secprovider.example", sla_target="15m P1 response", sla_status="At Risk"),
        m.Vendor(name="Firewall OEM", category="Security", contact="sales@fw-oem.example", sla_target="4h critical", sla_status="On Track"),
        m.Vendor(name="Local ISP (EU)", category="Connectivity", contact="noc@eu-isp.example", sla_target="99.5% uptime", sla_status="On Track"),
    ]
    s.add_all(vendors)
    s.flush()
    V = {v.name: v.id for v in vendors}

    # --- Programme: four service towers ---------------------------------
    specs = [
        dict(
            code="PRJ-WAN-001", name="Meridian Group Global WAN (EMEA) Managed Service",
            project_type="WAN", region="EMEA", status="Execution", health="Amber",
            budget=2_400_000, pct=52,
            business_case="Deliver a fully managed hybrid WAN underpinning Route 2020's cloud-first "
                          "direction (SAP and key apps moving to scalable cloud hosting).",
            scope="Fully managed hybrid WAN across client EMEA locations: primary MPLS with secondary "
                  "Internet (IPsec) backup; dual-MPLS with two CPE and provider POP diversity for "
                  "High-Availability sites (types E/F) and trusted datacentres; dual WAN-acceleration appliances; "
                  "24x7 operational, change and service management.",
            objectives="Meet 99.90% availability / 99.50% performance for High-Availability sites; "
                        "rationalise carriers; guarantee POP and local-tail diversity; reduce WAN opex.",
            deliverables="HLD/LLD, carrier order pack, site migration runbooks, as-built records, "
                         "SLA & service-management handover.",
            assumptions="Local tail providers available for POP diversity; change windows honoured.",
            constraints="Site type Q countries (e.g. China) where the Vendor may not deliver Internet "
                        "infrastructure; frozen change windows over quarter-end.",
            success_criteria="99.90%/99.50% SLA met on HA sites; zero P1 at cutover; validated POP/tail diversity.",
            phases=["Initiation", "HLD / LLD Design", "Carrier Procurement", "Build & Stage", "Site Migration", "Transition & Hypercare"],
            vendors=["Global MPLS Carrier", "Network Hardware OEM", "Local ISP (EU)"],
            risks=[
                ("POP / local-tail diversity unavailable in some metros", "N. Rao", "High", 4, 4,
                 "Engage second tail provider early; document exceptions with the client.", 18),
                ("Site type Q restriction blocks Internet secondary in China", "M. Silva", "High", 4, 5,
                 "Apply management exception; dual-MPLS with 50% secondary per RFP.", 25),
                ("MPLS tail circuit lead times slip the migration wave", "N. Rao", "Medium", 3, 4,
                 "Order circuits at design freeze; 4G/LTE temporary failover.", 30),
            ],
            issues=[("Dual-CPE physical separation not met at one HA site", "N. Rao", "High", 4, 4,
                     "Re-cable to separate risers; re-validate diversity.", 6)],
            deps=[("Client to confirm trusted-datacentre change windows", "Client Sponsor", "Medium", 3, 4, 8)],
            migration=[(c, t) for c, t in COUNTRIES],
        ),
        dict(
            code="PRJ-LAN-002", name="Meridian Group Managed LAN / WLAN (Global)",
            project_type="LAN", region="Global", status="Execution", health="Green",
            budget=1_150_000, pct=34,
            business_case="Standardise and manage LAN/WLAN globally to support secure, flexible and "
                          "guest access aligned to the security segmentation model.",
            scope="Requirements analysis, topology design and installation of LAN/WLAN; switch and AP "
                  "lifecycle and configuration management; NAC / 802.1X; device backup; secure "
                  "segmentation policy on the LAN; wireless coverage for flexible and guest workers.",
            objectives="Standardised LAN/WLAN estate; NAC-based access; coverage for flexible (15%), "
                        "single-location (30%), factory (47%) and guest (8%) worker profiles.",
            deliverables="LAN/WLAN topology & design pack, install runbooks, NAC policy, as-built docs.",
            assumptions="Structured cabling in place; power/space available in comms rooms.",
            constraints="Factory-floor RF environments; production-hours access restrictions.",
            success_criteria="Segmentation enforced; NAC live; wireless coverage SLAs met at all sites.",
            phases=["Initiation", "Site Survey & Design", "Hardware Procurement", "Install & Config", "Cutover", "Hypercare"],
            vendors=["Network Hardware OEM", "Firewall OEM"],
            risks=[
                ("Factory-floor AP density insufficient for coverage", "L. Novak", "Medium", 3, 3,
                 "RF survey per site; add APs where needed.", 20),
                ("Guest WLAN segmentation gaps expose corporate VLANs", "P. Mehta", "High", 3, 4,
                 "Enforce guest isolation; validate with pen test.", 16),
            ],
            issues=[("Legacy access switches fail firmware baseline", "L. Novak", "Medium", 3, 3,
                     "Stage firmware upgrade before install.", 5)],
            deps=[("Client to provide comms-room access & cabling records", "Client Sponsor", "Medium", 3, 3, 10)],
            migration=[(c, "LAN/WLAN") for c, _ in COUNTRIES[:8]],
        ),
        dict(
            code="PRJ-UCC-003", name="Meridian Group UC&C Platform Rollout (Global)",
            project_type="Unified Communications", region="Global", status="Execution", health="Amber",
            budget=1_450_000, pct=45,
            business_case="Provide a single global UC&C service (IM, presence, desktop sharing, voice "
                          "and video) as a productivity and user-satisfaction pillar of Route 2020.",
            scope="Integrated UC&C on the enterprise UC platform: Instant Messaging, presence, desktop sharing, "
                  "point-to-point and conferencing Voice & Video, enterprise-voice add-on; migration of "
                  "K1 (7,300), E1 (9,400) and E3 (13,300) licences; adoption across worker profiles.",
            objectives="Retire legacy telephony; enable conferencing add-on; achieve end-user "
                        "satisfaction KPI (Apdex/perception) as a strategic pillar.",
            deliverables="Voice routing design, provisioning runbooks, adoption plan, training collateral.",
            assumptions="WAN QoS in place for voice; licence entitlements confirmed by the client.",
            constraints="UC platform vendor roadmap; factory-worker (47%) low-touch adoption.",
            success_criteria="Voice quality within targets; adoption per profile; user-satisfaction KPI met.",
            phases=["Initiation", "Design & Voice Routing", "Licensing & Provisioning", "Pilot", "Global Rollout", "Adoption & Hypercare"],
            vendors=["UC&C Platform Vendor", "Network Hardware OEM"],
            risks=[
                ("UC platform roadmap shift (vendor migration) mid-rollout", "R. Khan", "High", 3, 4,
                 "Track vendor roadmap; keep migration path option open.", 22),
                ("Factory-worker adoption (47% of base) lags target", "M. Silva", "Medium", 4, 3,
                 "Shared-device kiosks; floor-manager champions.", 28),
                ("Voice quality degradation over constrained WAN links", "N. Rao", "Medium", 3, 4,
                 "Enforce QoS/CAC; monitor Apdex per site.", 15),
            ],
            issues=[("Licence true-up gap on E3 conferencing add-on", "S. Iyer", "Medium", 3, 3,
                     "Reconcile entitlements with the client procurement.", 7)],
            deps=[("Client to confirm number ranges & carrier SIP trunks", "Client Procurement Lead", "High", 4, 4, 12)],
            migration=[(c, "UC&C Wave") for c, _ in COUNTRIES[:10]],
        ),
        dict(
            code="PRJ-SEC-004", name="Meridian Group Security Services & SOC (Global)",
            project_type="Security", region="Global", status="Execution", health="Red",
            budget=1_800_000, pct=28,
            business_case="Establish managed security services and a 24x7 SOC to protect the client's global "
                          "estate and support secure access anywhere, on any device.",
            scope="Secure segmentation and firewall firmware management; Intrusion Prevention; "
                  "vulnerability management (authenticated scans); threat-intelligence integration; "
                  "log management and retention; incident detection via SOC/SIEM; incident, emergency "
                  "and forensic response.",
            objectives="Stand up 24x7 SOC; enforce segmentation policy; run vuln-scan cadence; integrate "
                        "threat intel; meet log-retention compliance; reduce security incidents.",
            deliverables="Security architecture, segmentation policy, SIEM use-cases, IR playbooks, "
                         "vuln-management schedule, SOC service handover.",
            assumptions="Client provides asset inventory and scan credentials; log sources reachable.",
            constraints="EU data-residency/privacy for log storage; segmentation impact on legacy apps.",
            success_criteria="SOC live with agreed use-cases; 15m P1 response; log retention compliant.",
            phases=["Initiation", "Architecture & Policy", "SIEM / SOC Build", "Log Onboarding & Tuning", "Vuln & Threat Intel", "Hypercare"],
            vendors=["Managed SOC / SIEM Provider", "Firewall OEM"],
            risks=[
                ("SIEM log-source onboarding delayed, use-cases not live", "P. Mehta", "Critical", 5, 5,
                 "Prioritise crown-jewel sources; phased use-case go-live.", 10),
                ("EU data-residency constraints on log storage location", "M. Silva", "High", 4, 4,
                 "EU-region log store; DPA review with the client legal.", 14),
                ("Segmentation policy breaks legacy application flows", "P. Mehta", "High", 4, 4,
                 "Discovery + monitor-mode before enforce; staged rollout.", 20),
            ],
            issues=[("Scan credentials not yet provisioned by the client", "Client Sponsor", "High", 4, 4,
                     "Escalate; interim unauthenticated scans.", 4)],
            deps=[("Client to define vuln-scan scope & first-responder contacts", "Client Procurement Lead", "High", 4, 5, 6)],
            migration=[(c, "SOC Onboarding") for c, _ in COUNTRIES[:6]],
        ),
    ]

    for spec in specs:
        p = m.Project(
            code=spec["code"], name=spec["name"], customer="Meridian Group",
            project_type=spec["project_type"], region=spec["region"],
            pm_name="Siddharth Dutt", status=spec["status"], health=spec["health"],
            start_date=_d(-150), end_date=_d(180), budget=spec["budget"],
            percent_complete=spec["pct"],
            business_case=spec["business_case"], scope=spec["scope"],
            objectives=spec["objectives"], deliverables=spec["deliverables"],
            assumptions=spec["assumptions"], constraints=spec["constraints"],
            success_criteria=spec["success_criteria"],
        )
        s.add(p)
        s.flush()

        # Stakeholders (RFP-accurate) + RACI
        s.add_all([
            m.Stakeholder(project_id=p.id, name="Client Sponsor", org="Meridian Group", role="RFP Sponsor / Contact",
                          influence="High", interest="High", raci="A", contact="sponsor@meridiangroup.example"),
            m.Stakeholder(project_id=p.id, name="Client Procurement Lead", org="Meridian Group", role="Procurement Lead",
                          influence="High", interest="Medium", raci="C", contact="procurement@meridiangroup.example"),
            m.Stakeholder(project_id=p.id, name="Advisor PMO Lead", org="Advisory Partner Co", role="Advisor / PMO",
                          influence="Medium", interest="High", raci="C", contact="pmo@advisorypartner.example"),
            m.Stakeholder(project_id=p.id, name="Client Service Desk", org="Meridian Group", role="SPOC (operating model)",
                          influence="Low", interest="Medium", raci="I", contact="servicedesk@meridiangroup.example"),
            m.Stakeholder(project_id=p.id, name="Delivery Lead", org="SD Advisory", role="Tower Delivery",
                          influence="Medium", interest="High", raci="R", contact="delivery@sdadvisory.io"),
        ])

        # WBS tasks (EVM). Cost-behind on Red projects (CPI < 1).
        phases = spec["phases"]
        per = spec["budget"] / len(phases)
        overrun = 1.15 if spec["health"] == "Red" else (1.04 if spec["health"] == "Amber" else 0.97)
        for i, phase in enumerate(phases):
            pct = max(0, min(100, spec["pct"] + 40 - i * 16 + random.randint(-8, 8)))
            planned = round(per, 0)
            actual = round(planned * (pct / 100.0) * overrun * random.uniform(0.97, 1.06), 0)
            s.add(m.WBSTask(
                project_id=p.id, wbs_code=f"{i+1}.0", name=f"{phase}",
                phase=phase, owner=random.choice([r.name for r in resources]),
                start_date=_d(-140 + i * 26), end_date=_d(-140 + (i + 1) * 26),
                depends_on=f"{i}.0" if i else "", is_critical=(i in (1, 2, 4)),
                planned_cost=planned, actual_cost=actual, percent_complete=pct,
                status="Complete" if pct >= 100 else ("In Progress" if pct > 0 else "Not Started"),
            ))

        # Milestones
        s.add_all([
            m.Milestone(project_id=p.id, name="Design Baseline Approved", due_date=_d(-55), status="Done"),
            m.Milestone(project_id=p.id, name="Pilot / First Wave Live", due_date=_d(12), status="Pending"),
            m.Milestone(project_id=p.id, name="Global Rollout Complete", due_date=_d(140), status="Pending"),
            m.Milestone(project_id=p.id, name="Service Transition & SLA Live", due_date=_d(165), status="Pending"),
        ])

        # Allocations + timesheets
        for r in resources[:5]:
            s.add(m.Allocation(project_id=p.id, resource_id=r.id, allocation_pct=random.choice([25, 50, 75, 100])))
            for w in range(4):
                s.add(m.Timesheet(project_id=p.id, resource_id=r.id, week_ending=_d(-7 * (4 - w)),
                                  planned_hours=40, actual_hours=round(40 * random.uniform(0.85, 1.12), 1)))

        # Budget lines by month/category
        months = [(_d(-120 + 30 * k)).strftime("%Y-%m") for k in range(5)]
        for cat in ["Circuits/Connectivity", "Hardware", "Licensing", "Services", "Labour"]:
            for mth in months:
                planned = round(spec["budget"] / 25, 0)
                s.add(m.BudgetLine(project_id=p.id, category=cat, description=f"{cat} — {spec['project_type']}",
                                   planned=planned, actual=round(planned * random.uniform(0.7, 1.2), 0),
                                   forecast=round(planned * random.uniform(0.95, 1.12), 0), month=mth))

        # Purchase orders (tower-relevant vendors)
        for vname in spec["vendors"]:
            vid = V[vname]
            s.add(m.PurchaseOrder(project_id=p.id, vendor_id=vid, po_number=f"PO-{p.id}{vid:02d}",
                                  description=f"{vname} — {spec['project_type']} supply/service",
                                  amount=round(spec["budget"] / 7, 0),
                                  status=random.choice(["Open", "Delivered", "Invoiced"]),
                                  delivery_status=random.choice(["Pending", "Delivered"]),
                                  invoice_status=random.choice(["Pending", "Paid"])))

        # RAID — tower-specific
        for (title, owner, sev, prob, imp, mit, due) in spec["risks"]:
            s.add(m.RaidItem(project_id=p.id, category="Risk", title=title, owner=owner, severity=sev,
                             probability=prob, impact=imp, mitigation=mit, due_date=_d(due), status="Open"))
        for (title, owner, sev, prob, imp, mit, due) in spec["issues"]:
            s.add(m.RaidItem(project_id=p.id, category="Issue", title=title, owner=owner, severity=sev,
                             probability=prob, impact=imp, mitigation=mit, due_date=_d(due), status="Open"))
        for (title, owner, sev, prob, imp, due) in spec["deps"]:
            s.add(m.RaidItem(project_id=p.id, category="Dependency", title=title, owner=owner, severity=sev,
                             probability=prob, impact=imp, due_date=_d(due), status="Open"))
        s.add(m.RaidItem(project_id=p.id, category="Assumption",
                         title="Client Service Desk remains SPOC per standard operating model",
                         owner="M. Silva", severity="Low", probability=2, impact=2, status="Open"))

        # Change requests
        s.add_all([
            m.ChangeRequest(project_id=p.id, cr_number=f"CR-{p.id}01",
                            description="Add newly acquired sites to in-scope estate",
                            justification="Route 2020 M&A activity added locations.",
                            scope_impact="Additional sites", cost_impact=round(spec["budget"] * 0.05, 0),
                            schedule_impact_days=21, raised_by="Client Sponsor", approver="Client Procurement Lead",
                            status="Under Review", raised_on=_d(-10)),
            m.ChangeRequest(project_id=p.id, cr_number=f"CR-{p.id}02",
                            description="Uplift monitoring / reporting to enhanced SLA tier",
                            justification="Business-continuity pillar of Route 2020.",
                            scope_impact="Service tier", cost_impact=round(spec["budget"] * 0.03, 0),
                            schedule_impact_days=7, raised_by="Advisor PMO Lead", approver="Client Procurement Lead",
                            status="Approved", raised_on=_d(-30)),
        ])

        # Meetings + actions
        mtg = m.Meeting(project_id=p.id, title="Client Weekly Delivery Governance", meeting_date=_d(-3),
                        attendees="Siddharth Dutt, Client Sponsor, Advisor PMO Lead, Delivery Lead",
                        agenda="Progress vs plan, RAID, SLA readiness, decisions",
                        minutes="Reviewed migration wave plan and top risks; SLA reporting walkthrough.",
                        decisions="Proceed with phased wave cutover; escalate open client dependencies.")
        mtg.action_items = [
            m.ActionItem(description="Close out open client-side dependency", owner="Client Sponsor", due_date=_d(5), status="Open"),
            m.ActionItem(description="Circulate updated wave schedule", owner="S. Iyer", due_date=_d(2), status="Open"),
        ]
        s.add(mtg)

        # Migration sites (in-scope countries / waves)
        for k, (site, mtype) in enumerate(spec["migration"]):
            label = f"{site} [{mtype}]" if mtype in ("E", "F", "B", "B+", "Q") else site
            s.add(m.MigrationSite(project_id=p.id, migration_type=spec["project_type"], site=label,
                                  scheduled_date=_d(-20 + k * 12),
                                  status=random.choice(["Planned", "In Progress", "Migrated"]),
                                  rollback_plan="Revert to prior config from backup; fail back to primary path.",
                                  acceptance=random.choice(["Pending", "Accepted"])))

        # Quality
        s.add_all([
            m.QualityItem(project_id=p.id, item_type="Audit", finding="As-built documentation trailing build progress",
                          corrective_action="Documentation catch-up sprint", preventive_action="Document-as-you-build policy",
                          owner="S. Iyer", status="Open"),
            m.QualityItem(project_id=p.id, item_type="NCR", finding="One site install deviates from design standard",
                          corrective_action="Rework to standard", preventive_action="QA checklist at handover",
                          owner="Delivery Lead", status="Closed"),
        ])

        # Compliance (Red projects have fewer artefacts complete)
        target = {"Green": 9, "Amber": 7, "Red": 5}[spec["health"]]
        for j, art in enumerate(COMPLIANCE_ARTIFACTS):
            s.add(m.ComplianceItem(project_id=p.id, artifact=art, complete=(j < target)))

        # Lessons (mapped to RFP value pillars)
        s.add_all([
            m.LessonLearned(project_id=p.id, category="Success", summary="Early carrier/vendor engagement protected the wave schedule"),
            m.LessonLearned(project_id=p.id, category="Challenge", summary="Client-side dependencies (credentials, windows) drove most slippage"),
            m.LessonLearned(project_id=p.id, category="Recommendation", summary="Track user-experience Apdex from day one to evidence the UX pillar"),
        ])

    s.commit()
    s.close()
    print("Seeded Meridian Group programme: 4 delivery projects (WAN, LAN/WLAN, UC&C, Security) "
          "grounded in the RFP.")


if __name__ == "__main__":
    seed()
