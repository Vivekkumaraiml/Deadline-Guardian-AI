"""Unit tests for Chat Adapter and message parsing for ASI:One."""
import pytest
from deadline_guardian.agent.chat_adapter import ChatAdapter
from deadline_guardian.models import OpportunityType


@pytest.fixture
def adapter() -> ChatAdapter:
    return ChatAdapter()


def test_chat_adapter_help_command(adapter: ChatAdapter):
    for cmd in ["/help", "help", "hi", "hello", "start"]:
        msg = adapter.process_message(cmd)
        assert "Deadline Guardian AI" in msg
        assert "How to interact" in msg


def test_chat_adapter_process_query(adapter: ChatAdapter):
    query = "I am a 3rd year Computer Science student in India looking for hackathons"
    response = adapter.process_message(query)
    assert "Deadline Guardian AI Report" in response
    assert "Computer Science" in response
    assert "Checklist" in response


def test_chat_adapter_extracts_profile_heuristics(adapter: ChatAdapter):
    profile = adapter._extract_profile("2nd year biotechnology student in Europe looking for scholarships in genetics")
    assert profile.course == "Biotechnology"
    assert profile.year_of_study == "2nd Year"
    assert profile.location == "Europe"
    assert profile.opportunity_type == OpportunityType.SCHOLARSHIP


def test_chat_adapter_detects_url_and_invokes_direct_analysis(adapter: ChatAdapter):
    query = "Check eligibility for https://summerofcode.withgoogle.com for a 2nd year CS student"
    response = adapter.process_message(query)
    assert "Deadline Guardian AI Report" in response
    assert "summerofcode.withgoogle.com" in response
    assert "UNVERIFIED" in response or "Notice" in response
