"""
Opportunity Extractor & Parser.
Extracts structured opportunity data (title, deadline, eligibility, documents, steps)
from raw text or webpage content, and strictly assigns verification statuses.
"""

from datetime import date, datetime
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

from deadline_guardian.models import Opportunity, OpportunityType, VerificationStatus


class OpportunityExtractor:
    """Extracts and normalizes educational opportunity details from text or HTML."""

    MONTHS = {
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

    KNOWN_DOCUMENT_KEYWORDS = {
        "resume": "Resume / CV",
        "cv": "Curriculum Vitae (CV)",
        "transcript": "Official College Transcripts",
        "grade card": "Semester Grade Sheets",
        "mark sheet": "Academic Mark Sheets",
        "recommendation": "Letter of Recommendation (LOR)",
        "lor": "Faculty Recommendation Letter (LOR)",
        "statement of purpose": "Statement of Purpose (SOP)",
        "sop": "Statement of Purpose (SOP)",
        "essay": "Application Essays",
        "github": "GitHub / GitLab Profile & Code Samples",
        "portfolio": "Portfolio / Project Showcase Link",
        "id card": "Student Identity Card / College Proof",
        "bonafide": "Bonafide Student Certificate",
        "proposal": "Project Proposal / Concept Note",
    }

    @classmethod
    def extract_from_text(
        cls,
        text: str,
        source_url: Optional[str] = None,
        title_hint: Optional[str] = None,
    ) -> Opportunity:
        """
        Parses unstructured announcement text or webpage content into an Opportunity.
        Labels the output as UNVERIFIED_USER_INPUT unless official origin is established.
        """
        text_lower = text.lower()

        # 1. Detect Opportunity Type
        opp_type = cls._detect_opportunity_type(text_lower)

        # 2. Extract Deadline
        deadline_str, deadline_date, is_rolling = cls._extract_deadline(text)

        # 3. Detect Title & Organization
        title, organization = cls._extract_title_and_org(text, title_hint)

        # 4. Extract Required Documents
        documents = cls._extract_documents(text_lower)

        # 5. Extract Eligibility & Years
        eligible_courses, eligible_years, criteria = cls._extract_eligibility(text)

        # 6. Extract Application Steps
        steps = cls._extract_steps(text)

        # 7. Verification Status determination
        domain = ""
        if source_url:
            parsed = urlparse(source_url)
            domain = parsed.netloc

        verification_status = VerificationStatus.UNVERIFIED_USER_INPUT
        notes = (
            "⚠️ UNVERIFIED USER INPUT: This opportunity was extracted from user-supplied text or URL. "
            "Deadlines and eligibility criteria have NOT been independently verified by an official registrar."
        )

        return Opportunity(
            id=f"user-opp-{abs(hash(text[:100])) % 100000}",
            title=title,
            organization=organization,
            opportunity_type=opp_type,
            official_url=source_url or "https://source.unspecified",
            deadline=deadline_str or ("Rolling" if is_rolling else "TBD / Check official link"),
            deadline_date=deadline_date,
            is_rolling=is_rolling,
            location="See official requirements",
            eligible_courses=eligible_courses or ["Any / Unspecified"],
            eligible_years=eligible_years or ["Any / Unspecified"],
            eligibility_criteria=criteria or ["Review official guidelines on portal"],
            required_documents=documents or ["Standard Resume / CV", "Student Enrollment Proof"],
            application_steps=steps or ["Navigate to official application page", "Review requirements and apply"],
            verification_status=verification_status,
            source_domain=domain or "user-supplied",
            notes=notes,
        )

    @classmethod
    def _detect_opportunity_type(cls, text_lower: str) -> OpportunityType:
        if "hackathon" in text_lower or "hack" in text_lower or "coding challenge" in text_lower:
            return OpportunityType.HACKATHON
        if "scholarship" in text_lower or "grant" in text_lower or "financial aid" in text_lower or "fellowship" in text_lower:
            return OpportunityType.SCHOLARSHIP
        if "intern" in text_lower or "internship" in text_lower or "co-op" in text_lower or "trainee" in text_lower:
            return OpportunityType.INTERNSHIP
        return OpportunityType.INTERNSHIP

    @classmethod
    def _extract_deadline(cls, text: str) -> Tuple[Optional[str], Optional[date], bool]:
        """Looks for dates or rolling indications in text."""
        text_lower = text.lower()
        if "rolling" in text_lower or "apply asap" in text_lower or "applications open year-round" in text_lower:
            return "Rolling", None, True

        # Search for ISO format: YYYY-MM-DD
        iso_match = re.search(r"\b(202[5-9])[-/.](0[1-9]|1[0-2])[-/.](0[1-9]|[12]\d|3[01])\b", text)
        if iso_match:
            try:
                y, m, d = int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3))
                parsed_date = date(y, m, d)
                return parsed_date.isoformat(), parsed_date, False
            except ValueError:
                pass

        # Search for "Month Day, Year" or "Day Month Year"
        month_pattern = r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
        
        # Pattern 1: April 15, 2026 or April 15 2026
        p1 = re.search(rf"\b{month_pattern}\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:,)?\s+(202[5-9])\b", text, re.IGNORECASE)
        if p1:
            try:
                m_str, d_str, y_str = p1.group(1).lower(), p1.group(2), p1.group(3)
                m = cls.MONTHS[m_str]
                parsed_date = date(int(y_str), m, int(d_str))
                return parsed_date.isoformat(), parsed_date, False
            except (ValueError, KeyError):
                pass

        # Pattern 2: 15 April 2026 or 15th April 2026
        p2 = re.search(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+{month_pattern}(?:,)?\s+(202[5-9])\b", text, re.IGNORECASE)
        if p2:
            try:
                d_str, m_str, y_str = p2.group(1), p2.group(2).lower(), p2.group(3)
                m = cls.MONTHS[m_str]
                parsed_date = date(int(y_str), m, int(d_str))
                return parsed_date.isoformat(), parsed_date, False
            except (ValueError, KeyError):
                pass

        return None, None, False

    @classmethod
    def _extract_title_and_org(cls, text: str, title_hint: Optional[str] = None) -> Tuple[str, str]:
        if title_hint and len(title_hint.strip()) > 3:
            return title_hint.strip(), "Organization (Extracted)"

        lines = [line.strip() for line in text.splitlines() if len(line.strip()) > 3]
        if lines:
            first_line = lines[0]
            clean_title = re.sub(r"^[#\s*_-]+", "", first_line)[:80]
            return clean_title, "Organization (Extracted)"

        return "User Provided Opportunity", "External Source"

    @classmethod
    def _extract_documents(cls, text_lower: str) -> List[str]:
        found_docs = []
        for kw, doc_name in cls.KNOWN_DOCUMENT_KEYWORDS.items():
            if kw in text_lower and doc_name not in found_docs:
                found_docs.append(doc_name)
        return found_docs

    @classmethod
    def _extract_eligibility(cls, text: str) -> Tuple[List[str], List[str], List[str]]:
        text_lower = text.lower()
        courses: List[str] = []
        years: List[str] = []
        criteria: List[str] = []

        # Course detection
        if any(w in text_lower for w in ["computer science", "cs", "software", "it"]):
            courses.append("Computer Science / IT")
        if any(w in text_lower for w in ["engineering", "stem", "b.tech", "b.e"]):
            courses.append("Engineering / STEM")
        if "data science" in text_lower or "artificial intelligence" in text_lower or "ai" in text_lower:
            courses.append("Data Science / AI")

        # Year detection
        if "1st year" in text_lower or "first year" in text_lower or "freshman" in text_lower:
            years.append("1st Year")
        if "2nd year" in text_lower or "second year" in text_lower:
            years.append("2nd Year")
        if "3rd year" in text_lower or "third year" in text_lower or "pre-final" in text_lower:
            years.append("3rd Year")
        if "final year" in text_lower or "4th year" in text_lower:
            years.append("Final Year")
        if "postgraduate" in text_lower or "masters" in text_lower:
            years.append("Postgraduate")

        # Extract criteria lines
        lines = text.splitlines()
        for line in lines:
            line_str = line.strip()
            if any(key in line_str.lower() for key in ["eligible", "eligibility", "must be", "requirement", "minimum cgpa"]):
                clean_criterion = re.sub(r"^[-*•\d.]+\s*", "", line_str)
                if len(clean_criterion) > 8:
                    criteria.append(clean_criterion[:180])

        return courses, years, criteria[:5]

    @classmethod
    def _extract_steps(cls, text: str) -> List[str]:
        steps: List[str] = []
        lines = text.splitlines()
        for line in lines:
            line_strip = line.strip()
            # Look for numbered or step markers
            if re.match(r"^(?:step\s*\d+|[1-5]\.)\s+", line_strip, re.IGNORECASE):
                clean_step = re.sub(r"^(?:step\s*\d+[:.-]?|[1-5]\.)\s*", "", line_strip, flags=re.IGNORECASE)
                if len(clean_step) > 5:
                    steps.append(clean_step[:150])
        return steps[:5]
