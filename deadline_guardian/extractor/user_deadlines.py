"""
User Deadline Extractor.
Extracts user-supplied deadlines from conversational messages (e.g.,
"a scholarship form due on the 15th and two internship applications due at the end of the month"),
resolves relative dates against the current reference date, and builds actionable checklists.
"""

import calendar
from datetime import date, datetime, timedelta
import re
from typing import List, Optional, Tuple

from deadline_guardian.models import ChecklistItem, OpportunityType, UrgencyLevel


class UserDeadlineItem:
    """Represents a personal deadline provided by the user to track."""

    def __init__(
        self,
        title: str,
        opportunity_type: OpportunityType,
        deadline_str: str,
        deadline_date: Optional[date] = None,
        days_remaining: Optional[int] = None,
        urgency: UrgencyLevel = UrgencyLevel.UPCOMING,
        date_resolution_note: Optional[str] = None,
        checklist: Optional[List[ChecklistItem]] = None,
    ):
        self.title = title
        self.opportunity_type = opportunity_type
        self.deadline_str = deadline_str
        self.deadline_date = deadline_date
        self.days_remaining = days_remaining
        self.urgency = urgency
        self.date_resolution_note = date_resolution_note
        self.checklist = checklist or []


class UserDeadlineExtractor:
    """Extracts, normalizes, and schedules user-provided deadlines."""

    WORD_TO_NUM = {
        "a": 1,
        "an": 1,
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
    }

    MONTH_NAMES = {
        "jan": 1, "january": 1,
        "feb": 2, "february": 2,
        "mar": 3, "march": 3,
        "apr": 4, "april": 4,
        "may": 5,
        "jun": 6, "june": 6,
        "jul": 7, "july": 7,
        "aug": 8, "august": 8,
        "sep": 9, "september": 9,
        "oct": 10, "october": 10,
        "nov": 11, "november": 11,
        "dec": 12, "december": 12,
    }

    @classmethod
    def has_personal_deadlines(cls, text: str) -> bool:
        """Determines if the text contains personal deadlines supplied by the user."""
        lower = text.lower()
        if not re.search(r"\b(due|deadline|deadlines)\b", lower):
            return False

        has_target = any(
            w in lower
            for w in [
                "scholarship", "internship", "intern", "hackathon", "form",
                "application", "submission", "assignment", "report"
            ]
        )
        has_timeframe = any(
            w in lower
            for w in [
                "15th", "end of", "next", "tomorrow", "tonight", "month", "week",
                "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"
            ]
        ) or re.search(r"\b\d{1,2}(?:st|nd|rd|th)?\b", lower)

        return has_target and has_timeframe

    @classmethod
    def has_reminder_request(cls, text: str) -> bool:
        """Checks if the user asked to be reminded or notified."""
        lower = text.lower()
        return any(
            kw in lower
            for kw in [
                "remind", "reminder", "alarm", "notify", "notification",
                "keep track", "track my", "track these", "alert"
            ]
        )

    @classmethod
    def extract_deadlines(
        cls,
        text: str,
        reference_date: Optional[date] = None,
    ) -> List[UserDeadlineItem]:
        """Extracts all user-stated deadlines and generates preparation checklists."""
        today = reference_date or date.today()
        items: List[UserDeadlineItem] = []

        # Split text into candidate phrases / clauses
        clauses = re.split(r"[,;]|\band\b", text, flags=re.IGNORECASE)

        for raw_clause in clauses:
            clause = raw_clause.strip()
            if not re.search(r"\bdue\b", clause, flags=re.IGNORECASE):
                continue

            # Determine opportunity type
            clause_lower = clause.lower()
            if "scholarship" in clause_lower or "grant" in clause_lower:
                opp_type = OpportunityType.SCHOLARSHIP
                base_title = "Scholarship Application Form" if "form" in clause_lower else "Scholarship Application"
            elif "intern" in clause_lower:
                opp_type = OpportunityType.INTERNSHIP
                base_title = "Internship Application"
            elif "hack" in clause_lower:
                opp_type = OpportunityType.HACKATHON
                base_title = "Hackathon Project Submission"
            else:
                opp_type = OpportunityType.ALL
                base_title = "Application Submission"

            # Determine count
            count = 1
            count_match = re.search(
                r"\b(a|an|one|two|three|four|five|\d+)\s+(?:[a-z0-9_-]+\s+){0,3}(?:scholarship|internship|intern|hackathon|application|form)",
                clause,
                flags=re.IGNORECASE,
            )
            if count_match:
                token = count_match.group(1).lower()
                count = cls.WORD_TO_NUM.get(token, int(token) if token.isdigit() else 1)

            # Resolve deadline
            deadline_str, deadline_date, note = cls._resolve_date(clause, today)

            # Calculate days and urgency
            days_remaining: Optional[int] = None
            if deadline_date:
                days_remaining = (deadline_date - today).days
                if days_remaining < 0:
                    urgency = UrgencyLevel.EXPIRED_OR_UNKNOWN
                elif days_remaining < 7:
                    urgency = UrgencyLevel.CRITICAL
                elif days_remaining <= 30:
                    urgency = UrgencyLevel.UPCOMING
                else:
                    urgency = UrgencyLevel.RELAXED
            else:
                urgency = UrgencyLevel.UPCOMING

            for i in range(count):
                title = base_title
                if count > 1:
                    title = f"{base_title} #{i + 1}"

                checklist = cls._generate_checklist(opp_type, title, deadline_str, days_remaining, urgency)
                items.append(
                    UserDeadlineItem(
                        title=title,
                        opportunity_type=opp_type,
                        deadline_str=deadline_str,
                        deadline_date=deadline_date,
                        days_remaining=days_remaining,
                        urgency=urgency,
                        date_resolution_note=note,
                        checklist=checklist,
                    )
                )

        # Sort items chronologically by days remaining (most urgent first)
        items.sort(key=lambda it: it.days_remaining if it.days_remaining is not None else 999)
        return items

    @classmethod
    def _resolve_date(cls, text: str, today: date) -> Tuple[str, Optional[date], Optional[str]]:
        """Resolves date expressions (e.g. 'end of month', 'the 15th', 'April 15')."""
        lower = text.lower()

        # 1. "end of the month" / "end of this month" / "end of month"
        if re.search(r"end\s+of\s+(?:the|this)?\s*month", lower):
            _, last_day = calendar.monthrange(today.year, today.month)
            d = date(today.year, today.month, last_day)
            return d.strftime("%B %d, %Y"), d, f"Resolved to the last day of the current month ({d.strftime('%B %Y')})"

        # 2. "the 15th" or "on the 15th" (day without explicit month)
        day_match = re.search(r"due\s+(?:on|by|at)?\s*(?:the\s+)?(\d{1,2})(?:st|nd|rd|th)?\b", lower)
        if day_match:
            try:
                target_day = int(day_match.group(1))
                if 1 <= target_day <= 31:
                    if target_day >= today.day:
                        # Day is in the current month
                        _, max_days = calendar.monthrange(today.year, today.month)
                        actual_day = min(target_day, max_days)
                        d = date(today.year, today.month, actual_day)
                        note = f"Resolved to {d.strftime('%B %d, %Y')} (current month)"
                    else:
                        # Day has passed this month -> resolve to next month
                        nm = 1 if today.month == 12 else today.month + 1
                        ny = today.year + 1 if today.month == 12 else today.year
                        _, max_days = calendar.monthrange(ny, nm)
                        actual_day = min(target_day, max_days)
                        d = date(ny, nm, actual_day)
                        note = (
                            f"Resolved as next upcoming {target_day}th ({d.strftime('%B %d, %Y')}) "
                            f"since {today.strftime('%B')} {target_day} has already passed. "
                            f"Please clarify if you meant a different month."
                        )
                    return d.strftime("%B %d, %Y"), d, note
            except ValueError:
                pass

        # 3. Explicit Month + Day (e.g., "Nov 15" or "15th November 2026")
        for m_name, m_num in cls.MONTH_NAMES.items():
            # Pattern: Month Day
            p1 = re.search(rf"\b{m_name}\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:\s*,\s*(\d{{4}}))?\b", lower)
            if p1:
                day_val = int(p1.group(1))
                year_val = int(p1.group(2)) if p1.group(2) else today.year
                try:
                    d = date(year_val, m_num, day_val)
                    return d.strftime("%B %d, %Y"), d, None
                except ValueError:
                    pass

            # Pattern: Day Month
            p2 = re.search(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+{m_name}(?:\s*,\s*(\d{{4}}))?\b", lower)
            if p2:
                day_val = int(p2.group(1))
                year_val = int(p2.group(2)) if p2.group(2) else today.year
                try:
                    d = date(year_val, m_num, day_val)
                    return d.strftime("%B %d, %Y"), d, None
                except ValueError:
                    pass

        # Fallback if no specific date pattern matched
        return "Soon / Check portal", None, "Exact calendar date could not be unambiguously resolved; please provide specific month and day."

    @classmethod
    def _generate_checklist(
        cls,
        opp_type: OpportunityType,
        title: str,
        deadline_str: str,
        days_remaining: Optional[int],
        urgency: UrgencyLevel,
    ) -> List[ChecklistItem]:
        """Creates prioritized application checklist tailored to the opportunity type and days remaining."""
        checklist: List[ChecklistItem] = []

        if opp_type == OpportunityType.SCHOLARSHIP:
            checklist.extend([
                ChecklistItem(
                    step_number=1,
                    task="Request faculty Letters of Recommendation (LOR) and official sealed transcripts",
                    deadline_hint="ASAP (High lead time: requires 7-14 days to process)",
                    urgency=urgency,
                    category="Documents",
                    completed=False,
                ),
                ChecklistItem(
                    step_number=2,
                    task="Draft and proofread Statement of Purpose (SOP) or scholarship essay",
                    deadline_hint="Complete at least 5 days before deadline",
                    urgency=urgency,
                    category="Profile & Writing",
                    completed=False,
                ),
                ChecklistItem(
                    step_number=3,
                    task="Gather financial eligibility proof, college bonafide certificate, and ID",
                    deadline_hint="Within 7 days",
                    urgency=urgency,
                    category="Documents",
                    completed=False,
                ),
                ChecklistItem(
                    step_number=4,
                    task=f"Submit complete scholarship application on official portal by {deadline_str}",
                    deadline_hint="Submit at least 24 hours prior to avoid portal slowdowns",
                    urgency=urgency,
                    category="Submission",
                    completed=False,
                ),
            ])
        elif opp_type == OpportunityType.INTERNSHIP:
            checklist.extend([
                ChecklistItem(
                    step_number=1,
                    task="Tailor Resume/CV to match the internship job description and required tech stack",
                    deadline_hint="Immediate / Within 48 hours",
                    urgency=urgency,
                    category="Profile & Writing",
                    completed=False,
                ),
                ChecklistItem(
                    step_number=2,
                    task="Verify live links to portfolio projects, GitHub demo repositories, and LinkedIn profile",
                    deadline_hint="Within 3 days",
                    urgency=urgency,
                    category="Portfolio",
                    completed=False,
                ),
                ChecklistItem(
                    step_number=3,
                    task="Draft concise responses for role-specific short answer and cover letter prompts",
                    deadline_hint="Day 4-5",
                    urgency=urgency,
                    category="Application Form",
                    completed=False,
                ),
                ChecklistItem(
                    step_number=4,
                    task=f"Review all attachments and submit internship application before {deadline_str}",
                    deadline_hint="🚨 CRITICAL: Submit at least 24 hours in advance",
                    urgency=urgency,
                    category="Submission",
                    completed=False,
                ),
            ])
        else:
            checklist.extend([
                ChecklistItem(
                    step_number=1,
                    task="Review eligibility requirements, required documentation, and submission guidelines",
                    deadline_hint="ASAP",
                    urgency=urgency,
                    category="Preparation",
                    completed=False,
                ),
                ChecklistItem(
                    step_number=2,
                    task="Gather required application artifacts and write draft submissions",
                    deadline_hint="Midway to deadline",
                    urgency=urgency,
                    category="Documents",
                    completed=False,
                ),
                ChecklistItem(
                    step_number=3,
                    task=f"Complete final review and submit before {deadline_str}",
                    deadline_hint="Submit at least 24 hours prior",
                    urgency=urgency,
                    category="Submission",
                    completed=False,
                ),
            ])

        return checklist
