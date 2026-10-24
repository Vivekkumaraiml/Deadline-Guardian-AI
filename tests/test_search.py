"""Unit tests for Search Providers, Live Search Mocks, and Factory."""
from unittest.mock import MagicMock, patch
import pytest
from deadline_guardian.config import settings
from deadline_guardian.models import OpportunityType, StudentProfile, VerificationStatus
from deadline_guardian.search.factory import (
    get_resolved_search_mode_description,
    get_search_provider,
)
from deadline_guardian.search.mock_provider import MockSearchProvider
from deadline_guardian.search.sample_data import SAMPLE_OPPORTUNITIES
from deadline_guardian.search.serper_provider import SerperSearchProvider
from deadline_guardian.search.tavily_provider import TavilySearchProvider


@pytest.fixture
def cs_student_profile() -> StudentProfile:
    return StudentProfile(
        course="Computer Science",
        year_of_study="3rd Year",
        interests=["AI", "Open Source"],
        location="India",
        opportunity_type=OpportunityType.ALL,
    )


def test_mock_search_filters_hackathons(cs_student_profile: StudentProfile):
    provider = MockSearchProvider()
    cs_student_profile.opportunity_type = OpportunityType.HACKATHON
    results = provider.search(profile=cs_student_profile, limit=5)
    assert len(results) > 0
    for opp in results:
        assert opp.opportunity_type == OpportunityType.HACKATHON


def test_mock_search_filters_scholarships(cs_student_profile: StudentProfile):
    provider = MockSearchProvider()
    cs_student_profile.opportunity_type = OpportunityType.SCHOLARSHIP
    results = provider.search(profile=cs_student_profile, limit=5)
    assert len(results) > 0
    for opp in results:
        assert opp.opportunity_type == OpportunityType.SCHOLARSHIP


def test_mock_search_keyword_relevance(cs_student_profile: StudentProfile):
    provider = MockSearchProvider()
    results = provider.search(profile=cs_student_profile, keywords="Google", limit=2)
    assert len(results) > 0
    assert any("Google" in opp.title or "Google" in opp.organization for opp in results)


def test_factory_returns_mock_when_forced():
    provider = get_search_provider(force_mock=True)
    assert isinstance(provider, MockSearchProvider)


def test_factory_selects_tavily_when_mock_disabled_and_key_provided(monkeypatch):
    monkeypatch.setattr(settings, "MOCK_SEARCH_MODE", False)
    monkeypatch.setattr(settings, "TAVILY_API_KEY", "test_tavily_key_123")
    monkeypatch.setattr(settings, "SERPER_API_KEY", None)

    provider = get_search_provider()
    assert isinstance(provider, TavilySearchProvider)


def test_factory_selects_serper_when_tavily_absent_and_serper_key_provided(monkeypatch):
    monkeypatch.setattr(settings, "MOCK_SEARCH_MODE", False)
    monkeypatch.setattr(settings, "TAVILY_API_KEY", None)
    monkeypatch.setattr(settings, "SERPER_API_KEY", "test_serper_key_456")

    provider = get_search_provider()
    assert isinstance(provider, SerperSearchProvider)


def test_factory_falls_back_to_mock_when_keys_missing(monkeypatch):
    monkeypatch.setattr(settings, "MOCK_SEARCH_MODE", False)
    monkeypatch.setattr(settings, "TAVILY_API_KEY", None)
    monkeypatch.setattr(settings, "SERPER_API_KEY", None)

    provider = get_search_provider()
    assert isinstance(provider, MockSearchProvider)


def test_factory_resolved_search_mode_description(monkeypatch):
    monkeypatch.setattr(settings, "MOCK_SEARCH_MODE", True)
    desc = get_resolved_search_mode_description()
    assert "Mock" in desc

    monkeypatch.setattr(settings, "MOCK_SEARCH_MODE", False)
    monkeypatch.setattr(settings, "TAVILY_API_KEY", "key")
    desc_live = get_resolved_search_mode_description()
    assert "Tavily" in desc_live


@patch("requests.post")
def test_tavily_search_provider_with_mock_api(mock_post: MagicMock, cs_student_profile: StudentProfile):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "results": [
            {
                "title": "Mocked Tech Fellowship 2026",
                "url": "https://example.org/fellowship",
                "content": "A prestigious fellowship for computer science students with deadline in June 2026.",
            }
        ]
    }
    provider = TavilySearchProvider(api_key="mock_test_key")
    results = provider.search(profile=cs_student_profile, limit=1)

    assert len(results) == 1
    opp = results[0]
    assert opp.title == "Mocked Tech Fellowship 2026"
    assert opp.official_url == "https://example.org/fellowship"
    assert opp.verification_status == VerificationStatus.SOURCE_REPORTED
    assert "example.org" in opp.source_domain


@patch("requests.post")
def test_serper_search_provider_with_mock_api(mock_post: MagicMock, cs_student_profile: StudentProfile):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "organic": [
            {
                "title": "Google AI Hackathon 2026",
                "link": "https://ai.google.dev/competition",
                "snippet": "Join the global hackathon for AI builders. Apply before May 1.",
            }
        ]
    }
    provider = SerperSearchProvider(api_key="mock_serper_key")
    results = provider.search(profile=cs_student_profile, limit=1)

    assert len(results) == 1
    opp = results[0]
    assert opp.title == "Google AI Hackathon 2026"
    assert opp.official_url == "https://ai.google.dev/competition"
    assert opp.verification_status == VerificationStatus.SOURCE_REPORTED
