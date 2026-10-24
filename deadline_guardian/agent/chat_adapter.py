"""
Chat Adapter for Deadline Guardian AI.
Parses natural language user prompts from ASI:One into structured inputs,
invokes the DeadlineGuardianService, and formats responses into clear Markdown.
"""

from datetime import date
import re
from typing import List, Optional, Tuple

from deadline_guardian.models import (
    GuardianAnalysisResponse,
    OpportunityReport,
    OpportunityType,
    StudentProfile,
    UrgencyLevel,
)
from deadline_guardian.service import DeadlineGuardianService


class ChatAdapter:
    """Bridges natural language chat messages to the core Deadline Guardian service."""

    def __init__(self, service: Optional[DeadlineGuardianService] = None):
        self.service = service or DeadlineGuardianService()

    def process_message(self, message: str) -> str:
        """Takes an inbound user chat message and returns an actionable Markdown response."""
        text = message.strip()
        if not text:
            return self.get_help_message()

        lower = text.lower()
        if lower in ("/help", "help", "hi", "hello", "start"):
            return self.get_help_message()

        # Check for URL or direct opportunity verification
        url_match = re.search(r"https?://[^\s]+", text)
        if url_match or "check this" in lower or "verify" in lower:
            profile = self._extract_profile(text)
            direct_target = url_match.group(0) if url_match else text
            result = self.service.analyze_direct_opportunity(profile, direct_target)
            return self.format_response_to_markdown(result)

        # Standard discovery query
        profile = self._extract_profile(text)
        result = self.service.analyze_profile(profile)
        return self.format_response_to_markdown(result)

    def _extract_profile(self, text: str) -> StudentProfile:
        """Heuristically parses degree, year, interests, location, and type from prompt."""
        text_lower = text.lower()

        # 1. Opportunity Type
        if "scholarship" in text_lower:
            opp_type = OpportunityType.SCHOLARSHIP
        elif "hackathon" in text_lower or "hack" in text_lower:
            opp_type = OpportunityType.HACKATHON
        elif "intern" in text_lower or "internship" in text_lower:
            opp_type = OpportunityType.INTERNSHIP
        else:
            opp_type = OpportunityType.ALL

        # 2. Year of Study
        year = "3rd Year"  # Default assumption if unspecified
        if "1st year" in text_lower or "first year" in text_lower or "freshman" in text_lower:
            year = "1st Year"
        elif "2nd year" in text_lower or "second year" in text_lower or "sophomore" in text_lower:
            year = "2nd Year"
        elif "3rd year" in text_lower or "third year" in text_lower or "junior" in text_lower or "pre-final" in text_lower:
            year = "3rd Year"
        elif "4th year" in text_lower or "fourth year" in text_lower or "final year" in text_lower or "senior" in text_lower:
            year = "Final Year"
        elif "postgrad" in text_lower or "master" in text_lower or "m.tech" in text_lower or "phd" in text_lower:
            year = "Postgraduate"

        # 3. Course / Degree
        course = "Computer Science"
        if "mechanical" in text_lower:
            course = "Mechanical Engineering"
        elif "electrical" in text_lower or "electronics" in text_lower or "ece" in text_lower:
            course = "Electronics & Electrical Engineering"
        elif "biotechnology" in text_lower or "biotech" in text_lower:
            course = "Biotechnology"
        elif "civil" in text_lower:
            course = "Civil Engineering"
        elif "data science" in text_lower or "ai" in text_lower:
            course = "Data Science & Artificial Intelligence"
        elif "business" in text_lower or "bba" in text_lower or "mba" in text_lower:
            course = "Business & Management"
        elif "design" in text_lower or "ui/ux" in text_lower:
            course = "Design & Human Computer Interaction"
        elif "engineering" in text_lower or "b.tech" in text_lower or "b.e" in text_lower:
            course = "Engineering"

        # 4. Location
        location = "Global"
        if "india" in text_lower:
            location = "India"
        elif "usa" in text_lower or "united states" in text_lower or "america" in text_lower:
            location = "USA"
        elif "europe" in text_lower or "uk" in text_lower or "germany" in text_lower:
            location = "Europe"

        # 5. Interests
        interests: List[str] = []
        interest_keywords = [
            "ai", "ml", "web3", "blockchain", "open source", "robotics",
            "cybersecurity", "cloud", "iot", "fintech", "design", "mobile"
        ]
        for kw in interest_keywords:
            if re.search(rf"\b{re.escape(kw)}\b", text_lower):
                interests.append(kw.upper() if len(kw) <= 3 else kw.title())

        if not interests:
            interests = ["Software Development", "Problem Solving"]

        return StudentProfile(
            course=course,
            year_of_study=year,
            interests=interests,
            location=location,
            opportunity_type=opp_type,
        )

    def format_response_to_markdown(self, response: GuardianAnalysisResponse) -> str:
        """Formats the analysis into rich, human-readable Markdown for ASI:One chat."""
        lines: List[str] = []

        lines.append("## 🛡️ **Deadline Guardian AI Report**")
        lines.append(f"**Student Profile:** `{response.student_summary}`\n")

        # Warnings / Disclaimers
        if response.unverified_warnings:
            lines.append("### ⚠️ Notice & Verification Status")
            for w in response.unverified_warnings:
                lines.append(f"- {w}")
            lines.append("")

        if response.total_found == 0:
            lines.append("No opportunities matching your criteria were found. Try adjusting your course, location, or opportunity type.")
            return "\n".join(lines)

        lines.append(f"### 🎯 Found {response.total_found} Curated Opportunities & Action Plans\n")

        for idx, rep in enumerate(response.reports, 1):
            opp = rep.opportunity
            el = rep.eligibility

            # Urgency icon
            if "CRITICAL" in rep.urgency.value:
                urgency_icon = "🔴"
            elif "UPCOMING" in rep.urgency.value:
                urgency_icon = "🟡"
            elif "ROLLING" in rep.urgency.value:
                urgency_icon = "🔵"
            else:
                urgency_icon = "🟢"

            days_str = f"({rep.days_remaining} days left)" if rep.days_remaining is not None else ""
            deadline_display = opp.deadline or "Rolling"

            lines.append(f"---")
            lines.append(f"### {idx}. **{opp.title}** ({opp.organization})")
            lines.append(f"- **Type:** {opp.opportunity_type.value.capitalize()} | **Location:** {opp.location}")
            lines.append(f"- **Deadline:** {urgency_icon} **{deadline_display}** {days_str} [{rep.urgency.value}]")
            lines.append(f"- **Official Portal:** [{opp.source_domain or 'Visit Link'}]({opp.official_url})")
            lines.append(f"- **Verification:** `{opp.verification_status.value}`")
            lines.append(f"- **Eligibility Match:** **{el.status.value}** ({el.match_score}%)")
            lines.append(f"  - *Analysis:* {el.explanation}")

            if el.missing_criteria:
                lines.append(f"  - ⚠️ *Gaps to verify:* {'; '.join(el.missing_criteria)}")

            if opp.required_documents:
                lines.append(f"- **Required Artifacts:** {', '.join(opp.required_documents)}")

            # Prioritized Checklist
            lines.append("\n**📋 Prioritized Application Checklist:**")
            for item in rep.checklist:
                hint = f" *[{item.deadline_hint}]*" if item.deadline_hint else ""
                lines.append(f"  {item.step_number}. **[{item.category}]** {item.task}{hint}")

            lines.append("")

        # General Tips
        if response.general_tips:
            lines.append("### 💡 Strategic Application Advice")
            for tip in response.general_tips:
                lines.append(f"- {tip}")

        return "\n".join(lines)

    @classmethod
    def get_help_message(cls) -> str:
        return (
            "## 🛡️ Welcome to **Deadline Guardian AI**\n\n"
            "I help college students discover scholarships, internships, and hackathons, "
            "verify eligibility, track critical deadlines, and generate step-by-step application checklists.\n\n"
            "### 💬 How to interact with me:\n"
            "1. **Discover opportunities:**\n"
            "   * *\"I am a 2nd year CS student in India interested in AI. Find me hackathons and internships with deadlines.\"*\n"
            "   * *\"3rd year female engineering student looking for scholarships in India.\"*\n"
            "2. **Check a specific opportunity link or text:**\n"
            "   * *\"Check eligibility for https://summerofcode.withgoogle.com for a 2nd year mechanical student.\"*\n"
            "   * *\"Paste any job/scholarship announcement text and ask me to verify deadlines and generate a checklist.\"*\n\n"
            "Powered by Fetch.ai uAgents and compatible with **ASI:One** via the Agent Chat Protocol (ACP)."
        )
