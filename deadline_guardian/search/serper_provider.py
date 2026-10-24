"""
Google Serper Search API Provider.
Executes live Google Search queries when SERPER_API_KEY is configured.
"""

import logging
from typing import List, Optional
from urllib.parse import urlparse
import requests
from deadline_guardian.models import Opportunity, OpportunityType, StudentProfile, VerificationStatus
from deadline_guardian.search.base import BaseSearchProvider

logger = logging.getLogger(__name__)


class SerperSearchProvider(BaseSearchProvider):
    """Integrates with Serper.dev Google Search API for live web discovery."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.endpoint = "https://google.serper.dev/search"

    def search(
        self,
        profile: StudentProfile,
        keywords: Optional[str] = None,
        limit: int = 5,
    ) -> List[Opportunity]:
        opp_type = profile.opportunity_type.value if profile.opportunity_type != OpportunityType.ALL else "opportunities"
        query = f"{profile.course} {opp_type} {profile.location} deadline eligibility 2026 application"
        if keywords:
            query += f" {keywords}"

        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {"q": query, "num": limit}

        try:
            resp = requests.post(self.endpoint, headers=headers, json=payload, timeout=12)
            resp.raise_for_status()
            data = resp.json()
            organic = data.get("organic", [])

            opportunities: List[Opportunity] = []
            for idx, item in enumerate(organic[:limit]):
                url = item.get("link", "")
                title = item.get("title", f"Result {idx + 1}")
                snippet = item.get("snippet", "")
                domain = urlparse(url).netloc

                opp = Opportunity(
                    id=f"serper-{idx}-{abs(hash(url)) % 10000}",
                    title=title,
                    organization=domain.replace("www.", "").split(".")[0].capitalize(),
                    opportunity_type=(
                        profile.opportunity_type
                        if profile.opportunity_type != OpportunityType.ALL
                        else OpportunityType.SCHOLARSHIP
                    ),
                    official_url=url,
                    deadline="Check official page for latest date",
                    deadline_date=None,
                    is_rolling=True,
                    location=profile.location,
                    eligible_courses=[profile.course],
                    eligible_years=[profile.year_of_study],
                    eligibility_criteria=[snippet or "See source page"],
                    required_documents=["Application form", "Resume", "Transcripts"],
                    application_steps=[f"Open {url}", "Verify eligibility & deadline", "Submit via portal"],
                    verification_status=VerificationStatus.SOURCE_REPORTED,
                    source_domain=domain,
                    notes="Discovered via live Google Serper search. Confirm details on official domain."
                )
                opportunities.append(opp)

            return opportunities
        except Exception as e:
            logger.error("Serper search failed: %s", e)
            raise RuntimeError(f"Serper search API error: {e}") from e
