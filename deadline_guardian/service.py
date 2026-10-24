"""
Deadline Guardian AI Core Service.
Coordinates student profile evaluation, opportunity discovery, eligibility matching,
urgency ranking, and application checklist generation.
"""

from datetime import date
import logging
from typing import List, Optional
from urllib.parse import urlparse

from deadline_guardian.checklist.generator import ChecklistGenerator
from deadline_guardian.config import settings
from deadline_guardian.extractor.parser import OpportunityExtractor
from deadline_guardian.extractor.url_fetcher import URLFetcher
from deadline_guardian.matcher.eligibility import EligibilityMatcher
from deadline_guardian.models import (
    GuardianAnalysisResponse,
    Opportunity,
    OpportunityReport,
    StudentProfile,
    VerificationStatus,
)
from deadline_guardian.search.factory import get_search_provider

logger = logging.getLogger(__name__)


class DeadlineGuardianService:
    """End-to-end service coordinating the Deadline Guardian workflow."""

    def __init__(self, force_mock: Optional[bool] = None, reference_date: Optional[date] = None):
        self.search_provider = get_search_provider(force_mock=force_mock)
        self.reference_date = reference_date

    def analyze_profile(
        self,
        profile: StudentProfile,
        keywords: Optional[str] = None,
        limit: int = 4,
    ) -> GuardianAnalysisResponse:
        """
        Discovers matching opportunities for a student, checks eligibility,
        and produces prioritized checklists.
        """
        logger.info("Analyzing profile: %s", profile.summary())
        unverified_warnings: List[str] = []

        # Check search provider configuration
        if settings.MOCK_SEARCH_MODE and not settings.is_live_search_available():
            unverified_warnings.append(
                "ℹ️ Demo / Benchmark Mode Active: Results are generated from verified benchmark datasets. "
                "Configure TAVILY_API_KEY or SERPER_API_KEY in .env for live multi-portal discovery."
            )

        # 1. Discover Opportunities
        try:
            opportunities = self.search_provider.search(profile=profile, keywords=keywords, limit=limit)
        except Exception as e:
            logger.error("Search failed: %s", e)
            unverified_warnings.append(f"⚠️ Search error encountered: {e}. Falling back to sample directory.")
            from deadline_guardian.search.mock_provider import MockSearchProvider
            fallback = MockSearchProvider()
            opportunities = fallback.search(profile=profile, keywords=keywords, limit=limit)

        # 2. Match and generate reports
        reports: List[OpportunityReport] = []
        for opp in opportunities:
            report = self._build_report(opp, profile)
            reports.append(report)

            if opp.verification_status == VerificationStatus.UNVERIFIED_USER_INPUT:
                unverified_warnings.append(
                    f"⚠️ {opp.title}: Unverified source link. Please confirm deadline directly on {opp.official_url}."
                )

        # Sort reports by urgency and match score
        reports.sort(
            key=lambda r: (
                0 if "CRITICAL" in r.urgency.value else (1 if "UPCOMING" in r.urgency.value else 2),
                -r.eligibility.match_score
            )
        )

        tips = [
            "Request official transcripts and Letters of Recommendation at least 2 weeks before the earliest deadline.",
            "Always submit at least 24 hours in advance to avoid portal slowdowns and server timeouts.",
            "Verify the exact time-zone of the cutoff (e.g. 11:59 PM AOE, EST, or IST)."
        ]

        return GuardianAnalysisResponse(
            student_summary=profile.summary(),
            total_found=len(reports),
            reports=reports,
            unverified_warnings=list(dict.fromkeys(unverified_warnings)),  # deduplicate
            general_tips=tips,
        )

    def analyze_direct_opportunity(
        self,
        profile: StudentProfile,
        input_data: str,
    ) -> GuardianAnalysisResponse:
        """
        Analyzes a specific opportunity provided by the user as either a URL or raw text snippet.
        """
        input_clean = input_data.strip()
        unverified_warnings: List[str] = []

        is_url = input_clean.startswith(("http://", "https://", "www.")) or (
            len(input_clean.split()) == 1 and "." in input_clean and "/" in input_clean
        )

        if is_url:
            fetch_res = URLFetcher.fetch(input_clean)
            if fetch_res.get("error"):
                unverified_warnings.append(f"⚠️ Network fetch notice: {fetch_res['error']}. Attempting heuristic parse.")
                raw_text = input_clean
                source_url = input_clean
                title_hint = None
            else:
                raw_text = fetch_res.get("text") or input_clean
                source_url = fetch_res.get("url") or input_clean
                title_hint = fetch_res.get("title")
        else:
            raw_text = input_clean
            source_url = "User Pasted Text"
            title_hint = None

        opp = OpportunityExtractor.extract_from_text(
            text=raw_text,
            source_url=source_url,
            title_hint=title_hint if is_url else None,
        )

        unverified_warnings.append(
            "⚠️ UNVERIFIED INPUT: The following analysis is derived from user-supplied text or URL. "
            "Dates and eligibility requirements must be independently confirmed with the host organization."
        )

        report = self._build_report(opp, profile)

        return GuardianAnalysisResponse(
            student_summary=profile.summary(),
            total_found=1,
            reports=[report],
            unverified_warnings=unverified_warnings,
            general_tips=[
                "Confirm official dates with program coordinators before making financial or travel plans.",
                "Ensure your application materials reflect the specific evaluation rubric on the host website."
            ],
        )

    def _build_report(self, opp: Opportunity, profile: StudentProfile) -> OpportunityReport:
        eligibility = EligibilityMatcher.evaluate(profile, opp)
        urgency, days_remaining, checklist = ChecklistGenerator.generate(opp, self.reference_date)

        return OpportunityReport(
            opportunity=opp,
            eligibility=eligibility,
            urgency=urgency,
            days_remaining=days_remaining,
            checklist=checklist,
        )
