"""Unit tests for Extractor and URL Fetcher with network mocks."""
from datetime import date
from unittest.mock import MagicMock, patch
import pytest
from deadline_guardian.extractor.parser import OpportunityExtractor
from deadline_guardian.extractor.url_fetcher import URLFetcher
from deadline_guardian.models import OpportunityType, VerificationStatus


def test_extract_from_text_with_standard_date():
    raw_text = """
    Global AI Innovation Hackathon 2026
    Organized by Tech Foundation.
    Eligible: Open to 2nd year and 3rd year Computer Science students.
    Deadline: April 15, 2026.
    Requirements:
    - Must submit resume and GitHub repository link.
    - Statement of Purpose and Faculty LOR required.
    Step 1: Register on portal.
    Step 2: Submit demo video.
    """
    opp = OpportunityExtractor.extract_from_text(raw_text, source_url="https://external-blog.com/post")

    assert opp.opportunity_type == OpportunityType.HACKATHON
    assert opp.deadline_date == date(2026, 4, 15)
    assert opp.deadline == "2026-04-15"
    assert opp.verification_status == VerificationStatus.UNVERIFIED_USER_INPUT
    assert "⚠️ UNVERIFIED" in opp.notes
    assert any("Resume" in doc for doc in opp.required_documents)
    assert any("GitHub" in doc for doc in opp.required_documents)
    assert any("LOR" in doc for doc in opp.required_documents)
    assert len(opp.application_steps) >= 2


def test_extract_from_text_iso_date():
    raw_text = """
    Cybersecurity Research Internship
    Deadline: 2026-08-31
    Must submit resume and transcript.
    """
    opp = OpportunityExtractor.extract_from_text(raw_text)
    assert opp.deadline_date == date(2026, 8, 31)
    assert opp.deadline == "2026-08-31"
    assert opp.opportunity_type == OpportunityType.INTERNSHIP


def test_extract_rolling_deadline():
    raw_text = """
    Software Engineering Fellowship.
    Applications open on a rolling basis. Apply ASAP.
    Open to undergraduate students in any discipline.
    Documents needed: CV and transcript.
    """
    opp = OpportunityExtractor.extract_from_text(raw_text)
    assert opp.is_rolling is True
    assert opp.deadline == "Rolling"
    assert any("CV" in doc or "Resume" in doc for doc in opp.required_documents)


@patch("requests.get")
def test_url_fetcher_success(mock_get: MagicMock):
    html_content = """
    <!DOCTYPE html>
    <html>
    <head><title>Official Tech Scholarship 2026</title></head>
    <body>
        <h1>National Tech Scholarship</h1>
        <p>Eligibility: Undergraduate STEM students. Deadline: 2026-10-31.</p>
    </body>
    </html>
    """
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = html_content

    result = URLFetcher.fetch("https://officialscholarship.edu/apply")
    assert result["error"] is None
    assert result["title"] == "Official Tech Scholarship 2026"
    assert "STEM students" in result["text"]
    assert result["domain"] == "officialscholarship.edu"


def test_url_fetcher_handles_invalid_url():
    res = URLFetcher.fetch("https://invalid-non-existent-domain-12345.xyz")
    assert res["error"] is not None
    assert res["text"] is None
