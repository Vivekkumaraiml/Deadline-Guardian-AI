"""Search provider package for Deadline Guardian AI."""
from deadline_guardian.search.base import BaseSearchProvider
from deadline_guardian.search.factory import get_search_provider

__all__ = ["BaseSearchProvider", "get_search_provider"]
