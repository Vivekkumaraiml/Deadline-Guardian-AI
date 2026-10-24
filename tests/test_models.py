"""Unit tests for Deadline Guardian AI core data models."""
from datetime import date
import pytest
from deadline_guardian.models import (
    ChecklistItem,
    EligibilityCheckResult,
    EligibilityStatus,
    GuardianAnalysisResponse,
    Opportunity,
    OpportunityReport,
    OpportunityType,
    StudentProfile,
    UrgencyLevel,
    VerificationStatus,
)


@pytest.fixture
def sample_profile() -> StudentProfile:
    return StudentProfile(
        course="Computer Science",
        year_of_study="3rd Year",
        interests=["AI/ML", "Web3", "Open Source"],
        location="India",
        opportunity_type=OpportunityType.INTERNSHIP,
        cgpa_or_percentage=8.5,
    )


@pytest.fixture
def sample_opportunity() -> Opportunity:
    return Opportunity(
        id="test-opp-01",
        title="Open Source Summer Fellowship",
        organization="Global Tech Foundation",
        opportunity_type=OpportunityType.INTERNSHIP,
        official_url="https://foundation.org/summer-fellowship",
        deadline="2026-05-15",
        deadline_date=date(2026, 5, 15),
        is_rolling=False,
        location="Global / Remote",
        eligible_courses=["Computer Science", "Information Technology", "STEM"],
        eligible_years=["2nd Year", "3rd Year", "Final Year"],
        eligibility_criteria=["Must have minimum 7.0 CGPA", "Proficient in Python"],
        required_documents=["Resume / CV", "Official Transcripts", "Letter of Recommendation (LOR)"],
        application_steps=["Submit online application", "Interview with project mentor"],
        verification_status=VerificationStatus.VERIFIED_OFFICIAL,
        source_domain="foundation.org",
        notes="Stipend provided upon milestone completion."
    )


def test_student_profile_creation_and_summary(sample_profile: StudentProfile):
    assert sample_profile.course == "Computer Science"
    assert sample_profile.year_of_study == "3rd Year"
    assert len(sample_profile.interests) == 3
    assert sample_profile.cgpa_or_percentage == 8.5
    summary = sample_profile.summary()
    assert "Computer Science" in summary
    assert "India" in summary
    assert "AI/ML" in summary
    assert "internship" in summary


def test_student_profile_default_interests():
    profile = StudentProfile(
        course="Mechanical Engineering",
        year_of_study="1st Year",
    )
    assert profile.interests == []
    # Location must be None when not provided by user to avoid fabricated data
    assert profile.location is None
    assert profile.opportunity_type == OpportunityType.ALL
    assert "[Location Unspecified]" in profile.summary()


def test_opportunity_validation(sample_opportunity: Opportunity):
    assert sample_opportunity.id == "test-opp-01"
    assert sample_opportunity.verification_status == VerificationStatus.VERIFIED_OFFICIAL
    assert sample_opportunity.deadline_date == date(2026, 5, 15)
    assert sample_opportunity.is_rolling is False
    assert len(sample_opportunity.required_documents) == 3
    assert len(sample_opportunity.application_steps) == 2


def test_checklist_item_defaults():
    item = ChecklistItem(
        step_number=1,
        task="Obtain Transcripts from University Exam Cell",
        deadline_hint="ASAP (Takes 7-14 days to issue)",
        urgency=UrgencyLevel.CRITICAL,
        category="Document Gathering",
    )
    assert item.step_number == 1
    assert item.completed is False
    assert item.urgency == UrgencyLevel.CRITICAL
    assert item.category == "Document Gathering"


def test_opportunity_report_and_guardian_response(sample_opportunity: Opportunity, sample_profile: StudentProfile):
    eligibility = EligibilityCheckResult(
        opportunity_id=sample_opportunity.id,
        opportunity_title=sample_opportunity.title,
        status=EligibilityStatus.ELIGIBLE,
        match_score=92.5,
        matched_criteria=["Course matches Computer Science", "Academic year matches 3rd Year"],
        missing_criteria=[],
        warnings=[],
        explanation="High Match: You meet all core requirements.",
    )
    checklist = [
        ChecklistItem(
            step_number=1,
            task="Upload Resume",
            urgency=UrgencyLevel.UPCOMING,
        )
    ]
    report = OpportunityReport(
        opportunity=sample_opportunity,
        eligibility=eligibility,
        urgency=UrgencyLevel.UPCOMING,
        days_remaining=21,
        checklist=checklist,
    )
    assert report.days_remaining == 21
    assert len(report.checklist) == 1

    response = GuardianAnalysisResponse(
        student_summary=sample_profile.summary(),
        total_found=1,
        reports=[report],
        unverified_warnings=["Sample notice"],
        general_tips=["Apply early"],
    )
    assert response.total_found == 1
    assert len(response.reports) == 1
    assert len(response.unverified_warnings) == 1
    assert "UTC" in response.generated_at
