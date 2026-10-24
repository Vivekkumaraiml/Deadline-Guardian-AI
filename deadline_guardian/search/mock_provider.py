"""
Mock / Sample Search Provider.
Provides robust offline and test capability using verified benchmark opportunities.
Guarantees tests and core workflow can run without paid external API credentials.
"""

from typing import List, Optional
from deadline_guardian.models import Opportunity, OpportunityType, StudentProfile
from deadline_guardian.search.base import BaseSearchProvider
from deadline_guardian.search.sample_data import SAMPLE_OPPORTUNITIES


class MockSearchProvider(BaseSearchProvider):
    """
    Search provider that filters a curated repository of real educational opportunities.
    Does not make external network requests, making it deterministic and free of cost.
    """

    def __init__(self, opportunities: Optional[List[Opportunity]] = None):
        self._opportunities = opportunities or SAMPLE_OPPORTUNITIES

    def search(
        self,
        profile: StudentProfile,
        keywords: Optional[str] = None,
        limit: int = 5,
    ) -> List[Opportunity]:
        matched: List[tuple[float, Opportunity]] = []

        target_type = profile.opportunity_type
        student_course = (profile.course or "").lower()
        student_location = (profile.location or "").lower()
        student_year = (profile.year_of_study or "").lower()
        interests = [i.lower() for i in profile.interests]
        kw_term = (keywords or "").lower()

        for opp in self._opportunities:
            score = 0.0

            # 1. Type matching
            if target_type != OpportunityType.ALL:
                if opp.opportunity_type.value != target_type.value:
                    continue  # Strict filter by opportunity type if requested
                score += 20.0
            else:
                score += 10.0

            # 2. Location matching
            opp_loc = opp.location.lower()
            if not student_location or "global" in opp_loc or "remote" in opp_loc:
                score += 15.0
            elif any(token in opp_loc for token in student_location.split()):
                score += 25.0
            elif any(token in student_location for token in opp_loc.split()):
                score += 25.0

            # 3. Course matching
            opp_courses = [c.lower() for c in opp.eligible_courses]
            if not student_course or "any" in opp_courses:
                score += 15.0
            elif any(c in student_course or student_course in c for c in opp_courses):
                score += 25.0
            elif "engineering" in student_course and ("stem" in opp_courses or "engineering" in opp_courses):
                score += 20.0
            elif "computer" in student_course and ("stem" in opp_courses or "cs" in opp_courses or "it" in opp_courses):
                score += 25.0

            # 4. Year matching
            opp_years = [y.lower() for y in opp.eligible_years]
            if not student_year or not opp_years or any(y in student_year or student_year in y for y in opp_years):
                score += 15.0

            # 5. Interests / Keywords matching
            opp_text = f"{opp.title} {opp.organization} {opp.notes or ''} {' '.join(opp.eligibility_criteria)}".lower()
            for interest in interests:
                if interest in opp_text:
                    score += 10.0

            if kw_term and kw_term in opp_text:
                score += 20.0

            matched.append((score, opp))

        # Sort descending by relevance score
        matched.sort(key=lambda x: x[0], reverse=True)

        # Return top N opportunities
        results = [opp for score, opp in matched[:limit]]
        return results
