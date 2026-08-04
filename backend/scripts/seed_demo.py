"""
Create one realistic demo project so the platform can be evaluated in a
few minutes instead of an afternoon.

    cd backend && python -m scripts.seed_demo

The problem this solves: testing the engines by hand means inventing a
project, guessing milestone dates, back-dating an event, walking a claim
through four stages and waiting for an Engineer's determination - before
anything interesting appears on screen. That is a lot of typing to find
out whether the idea is any good.

This builds a job in a state where every screen has exactly one obvious
thing to look at, with dates computed relative to today so they stay
sensible whenever you run it:

  Compliance      a few submissions due this week, plus a small
                  pre-CEIP backlog to show how onboarding history reads
  Events          a late-access event with its 20.2.1 notice clock running
  Claims          a claim the Engineer has already determined
  Determinations  that determination's Notice of Dissatisfaction window
                  closing in 3 days  <- the one that costs real money
  Variations      an instruction that changed the Works without being
                  called a Variation, notice still outstanding

Safe to run more than once - each run creates its own project with a
unique code, and touches nothing else.
"""

from datetime import date, time, timedelta
from uuid import uuid4

from app.constants.claim_status import ClaimResponseType, ClaimType
from app.constants.event_types import EventType
from app.constants.variation import VariationOrigin
from app.db.database import SessionLocal
from app.schemas.claim import (
    ClaimCreate,
    DetailedClaimSubmitRequest,
    EngineerDecisionRequest,
    NoticeSubmitRequest,
)
from app.schemas.determination import DeterminationReceivedRequest
from app.constants.determination import DeterminationOutcome
from app.schemas.event import EventCreate
from app.schemas.project import ProjectCreate, ProjectMilestonesUpdate
from app.schemas.variation import VariationCreate
from app.services import (
    claim_service,
    compliance_service,
    determination_service,
    event_service,
    notification_service,
    project_service,
    variation_service,
)
from app.services.claim_clock_service import get_today


def seed() -> None:
    db = SessionLocal()
    today = get_today()

    try:
        # --- the project -------------------------------------------------
        # Commenced three months ago, so the register has both live
        # obligations and a short pre-CEIP backlog.
        project = project_service.create_project(
            db,
            ProjectCreate(
                project_code=f"DEMO-{uuid4().hex[:4].upper()}",
                project_name="NR6 Skun - Kampong Cham Widening (DEMO)",
                client_name="Ministry of Public Works and Transport",
                contractor_name="Demo Construction Co., Ltd",
                engineer_name="Demo Engineering Consultants",
                contract_type="FIDIC Red Book 2017",
                contract_no="MPWT/NR6/2026/011",
                site_address="National Road 6, Kampong Cham",
                country="Cambodia",
                city="Kampong Cham",
                planned_start=today - timedelta(days=95),
                duration_days=540,
                currency="USD",
                contract_value=12_400_000,
            ),
        )
        project_service.update_milestones(
            db,
            project.id,
            ProjectMilestonesUpdate(
                letter_of_acceptance_date=today - timedelta(days=110),
                contract_edition="FIDIC 2017",
            ),
        )

        # --- Engine B: an event with its notice clock running ------------
        # 20 days ago, so the 28-day Sub-Clause 20.2.1 deadline is 8 days
        # away - close enough to be on the Deadlines screen, far enough
        # that it hasn't been missed.
        event = event_service.create_event_service(
            db,
            EventCreate(
                project_id=project.id,
                title="Soft alluvial clay found below formation at Ch. 9+200",
                description=(
                    "Trial pits show 1.8 m of soft alluvial clay well below "
                    "the depth indicated in the site investigation report. "
                    "Formation cannot be accepted without undercut and "
                    "replacement."
                ),
                event_date=today - timedelta(days=20),
                event_time=time(8, 30),
                event_type=EventType.UNFORESEEABLE_PHYSICAL_CONDITIONS.value,
                location="Ch. 9+150 to Ch. 9+320",
                severity="High",
                status="Open",
            ),
        )

        # --- Engine B: a claim the Engineer has already determined -------
        claim = claim_service.create_claim(
            db,
            ClaimCreate(
                project_id=project.id,
                claim_type=ClaimType.EOT_COST,
                claiming_party="Contractor",
                title="EOT and Cost - delayed access to Prey Chhor section",
                description=(
                    "Extension of Time and Cost arising from the Employer's "
                    "failure to give right of access within the time stated "
                    "in the Contract Data."
                ),
                governing_clause="Sub-Clause 2.1 - Right of Access to the Site",
                claim_basis=EventType.LATE_ACCESS_TO_SITE.value,
                awareness_date=today - timedelta(days=75),
                claimed_days=24,
                claimed_cost_amount=86_500,
            ),
        )
        claim_service.submit_notice(
            db,
            claim.id,
            NoticeSubmitRequest(notice_submitted_date=today - timedelta(days=60)),
        )
        claim_service.submit_detailed_claim(
            db,
            claim.id,
            DetailedClaimSubmitRequest(
                detailed_claim_submitted_date=today - timedelta(days=40),
                legal_basis_statement=(
                    "Sub-Clause 2.1: the Employer failed to give right of "
                    "access to, and possession of, the Site within the time "
                    "stated in the Contract Data. The Contractor is "
                    "accordingly entitled to EOT and Cost Plus Profit."
                ),
                particulars=(
                    "24 calendar days of critical delay to the embankment "
                    "activity, supported by daily records and the accepted "
                    "baseline programme."
                ),
                claimed_days=24,
            ),
        )
        # The Engineer determined it - partially. This opens the 3.7.5
        # window automatically (see contract_engine._on_engineer_responded).
        claim_service.engineer_respond(
            db,
            claim.id,
            EngineerDecisionRequest(
                response_type=ClaimResponseType.DETERMINATION,
                response_date=today - timedelta(days=27),
                days_granted=11,
                cost_awarded_amount=18_000,
                comment=(
                    "11 days EOT allowed. Cost limited to plant standing "
                    "time; profit and overhead rejected."
                ),
                responded_by="Demo Engineering Consultants",
            ),
        )

        # Correct the receipt date so the NOD window closes in 3 days -
        # the deadline this whole platform exists to catch. The letter was
        # dated 27 days ago; it reached site 25 days ago, and 25 + 28 = 3
        # days left, not 1.
        determination = determination_service.get_claim_determination(db, claim.id)
        if determination is not None:
            determination_service.record_determination_received(
                db,
                determination.id,
                DeterminationReceivedRequest(
                    determination_notice_date=today - timedelta(days=27),
                    determination_received_date=today - timedelta(days=25),
                    determination_summary=(
                        "11 days EOT allowed against 24 claimed. Cost "
                        "limited to plant standing time; profit and "
                        "overhead rejected."
                    ),
                    outcome=DeterminationOutcome.PARTIALLY_IN_FAVOUR,
                    days_determined=11,
                    cost_determined=18_000,
                ),
            )

        # --- Engine B: the Sub-Clause 3.5 trap ---------------------------
        # A drawing revision that changes the Works, issued without the
        # word "Variation" anywhere. Work has not started yet, so the
        # Notice can still be given in time - which is the whole point.
        variation_service.create_variation(
            db,
            VariationCreate(
                project_id=project.id,
                title="Revised pavement build-up, Ch. 8+000 to Ch. 11+500",
                description=(
                    "Drawing NR6-PAV-204 Rev C increases the base course "
                    "from 200 mm to 250 mm. Issued as a drawing revision "
                    "under cover of a routine transmittal - the word "
                    "Variation does not appear anywhere in it."
                ),
                origin=VariationOrigin.UNLABELLED_INSTRUCTION,
                instruction_reference="ENG-TRN-0442 / NR6-PAV-204 Rev C",
                instruction_date=today - timedelta(days=3),
                instruction_received_date=today - timedelta(days=2),
                work_commenced=False,
            ),
        )

        # --- let both engines run over it --------------------------------
        compliance_service.run_daily_tick(db, trigger_source="manual")

        summary = notification_service.unread_summary(db, project_id=project.id)
        register = compliance_service.get_register_summary(db, project.id)

        print(f"\nCreated: {project.project_name}")
        print(f"  open it at  /projects/{project.id}\n")
        print(f"  Alerts       {summary['total']} live "
              f"({summary['critical']} critical, {summary['warning']} warning)")
        print(f"  Compliance   {register['live_open']} live, "
              f"{register['historical_open']} pre-CEIP backlog")
        print(f"  Event        {event.event_no} - Sub-Clause 4.12, notice "
              f"due in {28 - 20} days, no claim raised yet")
        print(f"  Claim        {claim.claim_no} - determined, "
              f"NOD window closes in 3 days")
        print("  Variation    VO-001 - unlabelled instruction, 3.5 notice outstanding\n")
        print("  Start on the Deadlines page in the top bar.\n")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
