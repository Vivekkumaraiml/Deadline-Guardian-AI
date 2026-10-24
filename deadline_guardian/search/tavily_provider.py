"""
Tavily Search API Provider.
Executes live search queries against the web when a TAVILY_API_KEY is configured.
"""

import logging
from typing import List, Optional
from urllib.parse import urlparse
import requests
from deadline_guardian.models import Opportunity, OpportunityType, StudentProfile, VerificationStatus
from deadline_guardian.search.base import BaseSearchProvider

logger = logging.getLogger(__name__)


class TavilySearchProvider(BaseSearchProvider):
    """Integrates with Tavily AI Search API for real-time web discovery."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.endpoint = "https://api.tavily.com/search"

    def search(
        self,
        profile: StudentProfile,
        keywords: Optional[str] = None,
        limit: int = 5,
    ) -> List[Opportunity]:
        opp_type = profile.opportunity_type.value if profile.opportunity_type != OpportunityType.ALL else "opportunities"
        query_parts = [
            profile.course,
            opp_type,
            profile.location,
            "deadline",
            "eligibility",
            "requirements"
        ]
        if profile.interests:
            query_parts.append(" ".join(profile.interests[:2]))
        if keywords:
            query_parts.append(keywords)

        query = " ".join(query_parts)

        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "advanced",
            "include_answer": False,
            "max_results": max(limit * 2, 5),
        }

        try:
            resp = requests.post(self.endpoint, json=payload, timeout=12)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])

            opportunities: List[Opportunity] = []
            for idx, item in enumerate(results[:limit]):
                url = item.get("url", "")
                title = item.get("title", f"Discovered {profile.opportunity_type.value} {idx + 1}")
                content = item.get("content", "")
                parsed_url = urlparse(url)
                domain = parsed_url.netloc

                # Notice: Live search engine results are flagged as SOURCE_REPORTED unless verified
                opp = Opportunity(
                    id=f"tavily-{idx}-{abs(hash(url)) % 10000}",
                    title=title,
                    organization=domain.replace("www.", "").split(".")[0].capitalize(),
                    opportunity_type=(
                        profile.opportunity_type
                        if profile.opportunity_type != OpportunityType.ALL
                        else OpportunityType.INTERNSHIP
                    ),
                    official_url=url,
                    deadline="Check official page for latest date",
                    deadline_date=None,
                    is_rolling=True,
                    location=profile.location,
                    eligible_courses=[profile.course],
                    eligible_years=[profile.year_of_study],
                    eligibility_criteria=[
                        f"Reported in web search: {content[:200]}..." if len(content) > 200 else content or "Refer to source link"
                    ],
                    required_documents=["Resume / CV", "Official transcript (verify on site)"],
                    application_steps=[
                        f"Visit {url}",
                        "Verify current application cycle and deadline",
                        "Follow instructions on official portal"
                    ],
                    verification_status=VerificationStatus.SOURCE_REPORTED,
                    source_domain=domain,
                    notes="Discovered via live web search. Always confirm deadlines on the official page."
                )
                opportunities.append(opp)

            return opportunities
        except Exception as e:
            logger.error("Tavily search failed: %s", e)
            raise RuntimeError(f"Tavily search API error: {e}") from e
