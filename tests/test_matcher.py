"""Unit tests for Eligibility Matcher and transparent explanation engine."""
import pytest
from deadline_guardian.matcher.eligibility import EligibilityMatcher
from deadline_guardian.models import (
    EligibilityStatus,
    Opportunity,
    OpportunityType,
    StudentProfile,
    VerificationStatus,
)


@pytest.fixture
def cs_student() -> StudentProfile:
    return StudentProfile(
        course="Computer Science",
        year_of_study="3rd Year",
        interests=["AI", "Open Source"],
        location="India",
        opportunity_type=OpportunityType.INTERNSHIP,
    )


def test_high_eligibility_match(cs_student: StudentProfile):
    opp = Opportunity(
        id="test-cs-opp",
        title="CS Summer Internship",
        organization="Tech Corp",
        opportunity_type=OpportunityType.INTERNSHIP,
        official_url="https://techcorp.com",
        location="India",
        eligible_courses=["Computer Science", "Information Technology"],
        eligible_years=["3rd Year", "Final Year"],
        eligibility_criteria=["Must have good academic standing"],
        verification_status=VerificationStatus.VERIFIED_OFFICIAL,
    )

    result = EligibilityMatcher.evaluate(cs_student, opp)
    assert result.status == EligibilityStatus.ELIGIBLE
    assert result.match_score >= 75.0
    assert len(result.matched_criteria) >= 2
    assert len(result.missing_criteria) == 0
    assert "High Match" in result.explanation


def test_course_mismatch_low_score():
    civil_student = StudentProfile(
        course="Civil Engineering",
        year_of_study="1st Year",
        interests=["Construction"],
        location="USA",
        opportunity_type=OpportunityType.SCHOLARSHIP,
    )
    opp = Opportunity(
        id="test-cs-fellowship",
        title="Women in Technology CS Fellowship",
        organization="Adobe",
        opportunity_type=OpportunityType.SCHOLARSHIP,
        official_url="https://adobe.com",
        location="India",
        eligible_courses=["Computer Science", "Information Technology"],
        eligible_years=["3rd Year", "Pre-final Year"],
        eligibility_criteria=["Identifies as female", "Enrolled in Indian university"],
        verification_status=VerificationStatus.VERIFIED_OFFICIAL,
    )

    result = EligibilityMatcher.evaluate(civil_student, opp)
    assert result.status == EligibilityStatus.NOT_ELIGIBLE
    assert result.match_score < 45.0
    assert len(result.missing_criteria) > 0
    assert "Low Match" in result.explanation


def test_academic_year_gap_partial_match(cs_student: StudentProfile):
    # Student is 3rd Year, opportunity is strictly 1st/2nd Year
    opp = Opportunity(
        id="freshman-fellowship",
        title="Freshman Discovery Fellowship",
        organization="Research Institute",
        opportunity_type=OpportunityType.SCHOLARSHIP,
        official_url="https://institute.org",
        location="Global",
        eligible_courses=["Computer Science", "Engineering"],
        eligible_years=["1st Year", "2nd Year"],
        eligibility_criteria=["Must be in first two years of university"],
        verification_status=VerificationStatus.VERIFIED_OFFICIAL,
    )
    result = EligibilityMatcher.evaluate(cs_student, opp)
    assert result.status == EligibilityStatus.PARTIALLY_ELIGIBLE
    assert any("Academic Year Gap" in gap for gap in result.missing_criteria)
    assert "Moderate Match" in result.explanation


def test_global_location_matches_any_student(cs_student: StudentProfile):
    opp = Opportunity(
        id="global-hackathon",
        title="Global Web3 Hackathon",
        organization="Global Alliance",
        opportunity_type=OpportunityType.HACKATHON,
        official_url="https://globalhack.org",
        location="Global / Remote",
        eligible_courses=["Any"],
        eligible_years=["Any"],
        verification_status=VerificationStatus.VERIFIED_OFFICIAL,
    )
    result = EligibilityMatcher.evaluate(cs_student, opp)
    assert any("Location Eligible" in m for m in result.matched_criteria)
