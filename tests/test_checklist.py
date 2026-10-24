"""Unit tests for Checklist Generator and Urgency Priority Ranking."""
from datetime import date, timedelta
import pytest
from deadline_guardian.checklist.generator import ChecklistGenerator
from deadline_guardian.models import Opportunity, OpportunityType, UrgencyLevel, VerificationStatus


def test_calculate_urgency_levels():
    ref_date = date(2026, 4, 1)

    # 1. Critical (< 7 days)
    opp_critical = Opportunity(
        id="crit",
        title="Critical Hackathon",
        organization="Org",
        opportunity_type=OpportunityType.HACKATHON,
        official_url="https://test.org",
        deadline_date=ref_date + timedelta(days=4),
        deadline="2026-04-05",
        verification_status=VerificationStatus.VERIFIED_OFFICIAL,
    )
    urgency, days = ChecklistGenerator.calculate_urgency_and_days(opp_critical, reference_date=ref_date)
    assert urgency == UrgencyLevel.CRITICAL
    assert days == 4

    # 2. Upcoming (7-30 days)
    opp_upcoming = Opportunity(
        id="upc",
        title="Upcoming Internship",
        organization="Org",
        opportunity_type=OpportunityType.INTERNSHIP,
        official_url="https://test.org",
        deadline_date=ref_date + timedelta(days=20),
        deadline="2026-04-21",
        verification_status=VerificationStatus.VERIFIED_OFFICIAL,
    )
    urgency, days = ChecklistGenerator.calculate_urgency_and_days(opp_upcoming, reference_date=ref_date)
    assert urgency == UrgencyLevel.UPCOMING
    assert days == 20

    # 3. Relaxed (> 30 days)
    opp_relaxed = Opportunity(
        id="rel",
        title="Future Scholarship",
        organization="Org",
        opportunity_type=OpportunityType.SCHOLARSHIP,
        official_url="https://test.org",
        deadline_date=ref_date + timedelta(days=60),
        deadline="2026-05-31",
        verification_status=VerificationStatus.VERIFIED_OFFICIAL,
    )
    urgency, days = ChecklistGenerator.calculate_urgency_and_days(opp_relaxed, reference_date=ref_date)
    assert urgency == UrgencyLevel.RELAXED
    assert days == 60

    # 4. Rolling
    opp_rolling = Opportunity(
        id="roll",
        title="Rolling Opportunity",
        organization="Org",
        opportunity_type=OpportunityType.INTERNSHIP,
        official_url="https://test.org",
        is_rolling=True,
        verification_status=VerificationStatus.VERIFIED_OFFICIAL,
    )
    urgency, days = ChecklistGenerator.calculate_urgency_and_days(opp_rolling, reference_date=ref_date)
    assert urgency == UrgencyLevel.ROLLING
    assert days is None

    # 5. Expired
    opp_expired = Opportunity(
        id="exp",
        title="Expired Opportunity",
        organization="Org",
        opportunity_type=OpportunityType.INTERNSHIP,
        official_url="https://test.org",
        deadline_date=ref_date - timedelta(days=10),
        deadline="2026-03-22",
        verification_status=VerificationStatus.VERIFIED_OFFICIAL,
    )
    urgency, days = ChecklistGenerator.calculate_urgency_and_days(opp_expired, reference_date=ref_date)
    assert urgency == UrgencyLevel.EXPIRED_OR_UNKNOWN
    assert days == -10


def test_checklist_prioritizes_high_lead_time_documents():
    ref_date = date(2026, 4, 1)
    opp = Opportunity(
        id="opp-full",
        title="Fellowship with LOR and Transcripts",
        organization="Global Org",
        opportunity_type=OpportunityType.SCHOLARSHIP,
        official_url="https://fellowship.org",
        deadline_date=ref_date + timedelta(days=14),
        deadline="2026-04-15",
        required_documents=[
            "Official University Transcripts",
            "Two Letters of Recommendation (LOR)",
            "Statement of Purpose (SOP)",
            "Resume / CV"
        ],
        application_steps=[
            "Fill online bio data",
            "Upload proposal PDF"
        ],
        verification_status=VerificationStatus.VERIFIED_OFFICIAL,
    )

    urgency, days, items = ChecklistGenerator.generate(opp, reference_date=ref_date)
    assert urgency == UrgencyLevel.UPCOMING
    assert days == 14
    assert len(items) >= 4

    # High lead time documents must be in early steps
    first_tasks_str = " ".join([items[0].task, items[1].task]).lower()
    assert "transcript" in first_tasks_str or "recommendation" in first_tasks_str or "lor" in first_tasks_str

    # Final review & submission task must be included
    assert any(it.category == "Submission" for it in items)
