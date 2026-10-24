"""
Search Provider Factory.
Instantiates the appropriate search provider based on available credentials and configuration.
"""

import logging
from typing import Optional
from deadline_guardian.config import settings
from deadline_guardian.search.base import BaseSearchProvider
from deadline_guardian.search.mock_provider import MockSearchProvider
from deadline_guardian.search.tavily_provider import TavilySearchProvider
from deadline_guardian.search.serper_provider import SerperSearchProvider

logger = logging.getLogger(__name__)


def get_search_provider(
    force_mock: Optional[bool] = None,
    force_live: Optional[bool] = None,
) -> BaseSearchProvider:
    """
    Returns an initialized search provider.

    Precedence:
    1. If force_mock is True -> MockSearchProvider
    2. If force_live is True:
       - Uses Tavily if TAVILY_API_KEY is available
       - Uses Serper if SERPER_API_KEY is available
       - Falls back to MockSearchProvider with warning if no credentials configured
    3. If settings.MOCK_SEARCH_MODE is True -> MockSearchProvider
    4. If settings.TAVILY_API_KEY is available -> TavilySearchProvider
    5. If settings.SERPER_API_KEY is available -> SerperSearchProvider
    6. Fallback -> MockSearchProvider
    """
    if force_mock is True:
        logger.info("Using MockSearchProvider (forced mock mode).")
        return MockSearchProvider()

    if force_live is True:
        if settings.TAVILY_API_KEY:
            logger.info("Using TavilySearchProvider (forced live mode).")
            return TavilySearchProvider(api_key=settings.TAVILY_API_KEY)
        if settings.SERPER_API_KEY:
            logger.info("Using SerperSearchProvider (forced live mode).")
            return SerperSearchProvider(api_key=settings.SERPER_API_KEY)
        logger.warning(
            "Forced live search requested, but no live credentials found (TAVILY_API_KEY or SERPER_API_KEY). "
            "Falling back to MockSearchProvider."
        )
        return MockSearchProvider()

    if settings.MOCK_SEARCH_MODE:
        logger.info("Using MockSearchProvider (MOCK_SEARCH_MODE=true).")
        return MockSearchProvider()

    if settings.TAVILY_API_KEY:
        logger.info("Using TavilySearchProvider with configured API key.")
        return TavilySearchProvider(api_key=settings.TAVILY_API_KEY)

    if settings.SERPER_API_KEY:
        logger.info("Using SerperSearchProvider with configured API key.")
        return SerperSearchProvider(api_key=settings.SERPER_API_KEY)

    logger.warning("No search API credentials found. Falling back to MockSearchProvider.")
    return MockSearchProvider()


def get_resolved_search_mode_description(
    force_mock: Optional[bool] = None,
    force_live: Optional[bool] = None,
) -> str:
    """Returns a descriptive string explaining which search provider is active and why."""
    provider = get_search_provider(force_mock=force_mock, force_live=force_live)
    if isinstance(provider, MockSearchProvider):
        if force_mock:
            return "Mock (forced via --mock CLI flag)"
        if settings.MOCK_SEARCH_MODE:
            return "Mock (MOCK_SEARCH_MODE=true in .env)"
        return "Mock (Fallback - No live API keys configured in .env)"
    if isinstance(provider, TavilySearchProvider):
        return "Live (Tavily Search API)"
    if isinstance(provider, SerperSearchProvider):
        return "Live (Google Serper API)"
    return f"Active ({type(provider).__name__})"
