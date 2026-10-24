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


def get_search_provider(force_mock: Optional[bool] = None) -> BaseSearchProvider:
    """
    Returns an initialized search provider.

    Precedence:
    1. If force_mock is True -> MockSearchProvider
    2. If settings.MOCK_SEARCH_MODE is True -> MockSearchProvider
    3. If TAVILY_API_KEY is available -> TavilySearchProvider
    4. If SERPER_API_KEY is available -> SerperSearchProvider
    5. Fallback -> MockSearchProvider
    """
    if force_mock is True:
        logger.info("Using MockSearchProvider (forced mock mode).")
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
