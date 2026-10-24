"""Unit tests for Chat Adapter, message parsing, and personal deadline tracking for ASI:One."""
from datetime import date
import pytest

from deadline_guardian.agent.chat_adapter import ChatAdapter
from deadline_guardian.models import OpportunityType
from deadline_guardian.service import DeadlineGuardianService


@pytest.fixture
def adapter() -> ChatAdapter:
    service = DeadlineGuardianService(reference_date=date(2026, 10, 24))
    return ChatAdapter(service=service)


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


def test_personal_deadline_tracking_and_no_fabrication(adapter: ChatAdapter):
    """
    Evaluator Scenario:
    User asks to track upcoming deadlines: scholarship form due on the 15th and two internship
    applications due at the end of the month, with a request to be reminded.
    """
    query = (
        "Can you keep track of my upcoming deadlines? I have a scholarship form due on the 15th "
        "and two internship applications due at the end of the month. Please remind me as each approaches."
    )
    response = adapter.process_message(query)

    # 1. Must recognize and output Personal Deadline Tracking Report
    assert "Personal Deadline Tracking Report" in response

    # 2. Must not fabricate student profile
    assert "3rd Year Computer Science in Global" not in response
    assert "Not specified" in response

    # 3. Must track all 3 items (1 scholarship + 2 internships)
    assert "Scholarship Application Form" in response
    assert "Internship Application #1" in response
    assert "Internship Application #2" in response

    # 4. Must compute accurate days remaining relative to Oct 24, 2026
    # Internships due Oct 31 -> ~7 days left (CRITICAL)
    assert "~7 days left" in response or "7 days" in response
    assert "CRITICAL" in response

    # Scholarship due Nov 15 -> ~22 days left (UPCOMING)
    assert "~22 days left" in response or "22 days" in response
    assert "UPCOMING" in response

    # 5. Must provide prioritized action checklists
    assert "Prioritized Action Checklists" in response
    assert "Resume" in response or "transcripts" in response

    # 6. Must honestly disclose tracking/reminder limitations
    assert "Tracking & Reminder Limitations Notice" in response
    assert "persistent background push notifications" in response or "calendar alarms" in response
    assert "Google Calendar" in response or "personal calendar" in response


def test_no_profile_fabrication_when_details_omitted(adapter: ChatAdapter):
    profile = adapter._extract_profile("Find me scholarships and internships")
    assert profile.course is None
    assert profile.year_of_study is None
    assert profile.location is None
    assert profile.interests == []
    assert not profile.has_user_specified_details()

    response = adapter.process_message("Find me scholarships")
    assert "3rd Year Computer Science" not in response
    assert "Not specified" in response


def test_profile_with_partial_details_and_cgpa(adapter: ChatAdapter):
    profile = adapter._extract_profile("I'm a first-year student with a 7.2 CGPA looking for scholarships")
    assert profile.year_of_study == "1st Year"
    assert profile.cgpa_or_percentage == 7.2
    assert profile.course is None
    assert profile.location is None
    assert profile.has_user_specified_details()
