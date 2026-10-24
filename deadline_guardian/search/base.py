"""
Abstract Base Search Provider.
Defines interface for retrieving opportunities based on student profile or search keywords.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from deadline_guardian.models import Opportunity, StudentProfile


class BaseSearchProvider(ABC):
    """Abstract interface for all opportunity search backends."""

    @abstractmethod
    def search(
        self,
        profile: StudentProfile,
        keywords: Optional[str] = None,
        limit: int = 5,
    ) -> List[Opportunity]:
        """
        Search for relevant educational opportunities matching student criteria.

        Args:
            profile: The student profile containing course, year, interests, location.
            keywords: Optional additional search terms or query overrides.
            limit: Maximum number of opportunities to return.

        Returns:
            List of structured Opportunity objects.
        """
        pass
