"""Unit tests for Deadline Guardian Service workflow."""
from datetime import date
from unittest.mock import MagicMock, patch
import pytest
from deadline_guardian.models import OpportunityType, StudentProfile, VerificationStatus
from deadline_guardian.service import DeadlineGuardianService


@pytest.fixture
def service() -> DeadlineGuardianService:
    return DeadlineGuardianService(force_mock=True, reference_date=date(2026, 4, 1))


@pytest.fixture
def profile() -> StudentProfile:
    return StudentProfile(
        course="Computer Science",
        year_of_study="2nd Year",
        interests=["Open Source", "AI"],
        location="India",
        opportunity_type=OpportunityType.ALL,
    )


def test_service_analyze_profile_returns_valid_response(service: DeadlineGuardianService, profile: StudentProfile):
    res = service.analyze_profile(profile, limit=3)
    assert res.total_found > 0
    assert len(res.reports) > 0
    assert "Computer Science" in res.student_summary
    assert len(res.general_tips) > 0

    first_report = res.reports[0]
    assert first_report.eligibility.match_score >= 0.0
    assert len(first_report.checklist) > 0


def test_service_handles_search_failure_with_fallback(service: DeadlineGuardianService, profile: StudentProfile):
    # Mock search_provider.search to raise an error
    service.search_provider.search = MagicMock(side_effect=RuntimeError("Search API timeout"))
    res = service.analyze_profile(profile, limit=2)

    # Should fall back cleanly and report warning
    assert res.total_found > 0
    assert any("Search error encountered" in w for w in res.unverified_warnings)


def test_service_analyze_direct_pasted_text(service: DeadlineGuardianService, profile: StudentProfile):
    raw_snippet = """
    Hackathon 2026
    Organized by Blockchain Alliance.
    Deadline: 2026-06-15.
    Must submit GitHub link and Resume.
    """
    res = service.analyze_direct_opportunity(profile, raw_snippet)
    assert res.total_found == 1
    report = res.reports[0]
    assert report.opportunity.verification_status == VerificationStatus.UNVERIFIED_USER_INPUT
    assert any("UNVERIFIED" in w for w in res.unverified_warnings)
    assert report.opportunity.deadline == "2026-06-15"


@patch("deadline_guardian.service.URLFetcher.fetch")
def test_service_analyze_direct_url_with_mock(mock_fetch: MagicMock, service: DeadlineGuardianService, profile: StudentProfile):
    mock_fetch.return_value = {
        "url": "https://official.org/summer-ai",
        "domain": "official.org",
        "title": "Official Summer AI Fellowship",
        "text": "Summer AI Fellowship. Deadline: 2026-07-31. Requires resume and official transcript.",
        "error": None,
    }

    res = service.analyze_direct_opportunity(profile, "https://official.org/summer-ai")
    assert res.total_found == 1
    report = res.reports[0]
    assert report.opportunity.title == "Official Summer AI Fellowship"
    assert report.opportunity.source_domain == "official.org"
    assert report.opportunity.deadline == "2026-07-31"
