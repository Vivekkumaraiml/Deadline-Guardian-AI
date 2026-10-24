"""
Core Data Models for Deadline Guardian AI.
Uses Pydantic v2 for data validation, typing, and serialization.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class OpportunityType(str, Enum):
    SCHOLARSHIP = "scholarship"
    INTERNSHIP = "internship"
    HACKATHON = "hackathon"
    ALL = "all"


class VerificationStatus(str, Enum):
    VERIFIED_OFFICIAL = "VERIFIED_OFFICIAL"          # Confirmed directly from official domain/program page
    SOURCE_REPORTED = "SOURCE_REPORTED"              # Reported by aggregator/directory, check official page
    UNVERIFIED_USER_INPUT = "UNVERIFIED_USER_INPUT"  # Extracted from user pasted text/link without authoritative check
    EXPIRED_OR_TBD = "EXPIRED_OR_TBD"                # Deadline passed or announced as TBD


class EligibilityStatus(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    PARTIALLY_ELIGIBLE = "PARTIALLY_ELIGIBLE"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    REQUIRES_CHECK = "REQUIRES_CHECK"


class UrgencyLevel(str, Enum):
    CRITICAL = "CRITICAL (< 7 days)"
    UPCOMING = "UPCOMING (7-30 days)"
    RELAXED = "RELAXED (> 30 days)"
    ROLLING = "ROLLING (Apply ASAP)"
    EXPIRED_OR_UNKNOWN = "EXPIRED / UNKNOWN"


class StudentProfile(BaseModel):
    """Profile data representing a student searching for opportunities."""
    course: str = Field(..., description="Field of study or degree, e.g. 'Computer Science', 'Mechanical Engineering'")
    year_of_study: str = Field(..., description="Current year of college, e.g. '1st Year', '2nd Year', '3rd Year', 'Final Year'")
    interests: List[str] = Field(default_factory=list, description="Keywords or topics of interest, e.g. ['AI/ML', 'Web3', 'Open Source']")
    location: str = Field(default="Global", description="Student current country or residency, e.g. 'India', 'USA', 'Remote'")
    opportunity_type: OpportunityType = Field(default=OpportunityType.ALL, description="Filter: scholarship, internship, hackathon, or all")
    cgpa_or_percentage: Optional[float] = Field(default=None, description="Current CGPA or grade percentage if available")

    def summary(self) -> str:
        interests_str = ", ".join(self.interests) if self.interests else "General"
        return f"{self.year_of_study} {self.course} in {self.location} | Interests: {interests_str} | Looking for: {self.opportunity_type.value}"


class Opportunity(BaseModel):
    """Structured representation of an educational opportunity."""
    id: str = Field(..., description="Unique slug or identifier")
    title: str = Field(..., description="Official title of the opportunity")
    organization: str = Field(..., description="Hosting company, university, or foundation")
    opportunity_type: OpportunityType = Field(..., description="Type: scholarship, internship, or hackathon")
    official_url: str = Field(..., description="Authoritative official application or information URL")
    deadline: Optional[str] = Field(default=None, description="Deadline formatted string (e.g. '2026-04-15' or 'Rolling')")
    deadline_date: Optional[date] = Field(default=None, description="Parsed calendar deadline date if known")
    is_rolling: bool = Field(default=False, description="True if applications are accepted on a rolling basis")
    location: str = Field(default="Global", description="Target region or location constraints")
    eligible_courses: List[str] = Field(default_factory=list, description="Target degrees or fields (empty means any)")
    eligible_years: List[str] = Field(default_factory=list, description="Target academic years (empty means any)")
    eligibility_criteria: List[str] = Field(default_factory=list, description="Key eligibility bullet points")
    required_documents: List[str] = Field(default_factory=list, description="List of required application artifacts")
    application_steps: List[str] = Field(default_factory=list, description="Sequential steps to complete the application")
    verification_status: VerificationStatus = Field(default=VerificationStatus.SOURCE_REPORTED)
    source_domain: str = Field(default="", description="Hostname of source, e.g. 'summerofcode.withgoogle.com'")
    notes: Optional[str] = Field(default=None, description="Special instructions, stipend, or perks")


class EligibilityCheckResult(BaseModel):
    """Detailed result of matching student profile against an opportunity."""
    opportunity_id: str
    opportunity_title: str
    status: EligibilityStatus
    match_score: float = Field(..., ge=0.0, le=100.0, description="Confidence/match percentage")
    matched_criteria: List[str] = Field(default_factory=list)
    missing_criteria: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    explanation: str


class ChecklistItem(BaseModel):
    """An actionable, chronological preparation task."""
    step_number: int
    task: str
    deadline_hint: Optional[str] = None
    urgency: UrgencyLevel
    category: str = Field(default="Preparation", description="Category: 'Documents', 'Portfolio', 'Application Form', 'Submission'")
    completed: bool = False


class OpportunityReport(BaseModel):
    """Comprehensive evaluation combining the opportunity, eligibility, and checklist."""
    opportunity: Opportunity
    eligibility: EligibilityCheckResult
    urgency: UrgencyLevel
    days_remaining: Optional[int] = None
    checklist: List[ChecklistItem] = Field(default_factory=list)


class GuardianAnalysisResponse(BaseModel):
    """Full analysis delivered to user or ASI:One chat."""
    student_summary: str
    total_found: int
    reports: List[OpportunityReport] = Field(default_factory=list)
    unverified_warnings: List[str] = Field(default_factory=list)
    general_tips: List[str] = Field(default_factory=list)
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
