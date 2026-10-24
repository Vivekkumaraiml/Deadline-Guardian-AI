"""
URL Fetcher utility.
Safely downloads and extracts readable text and metadata from user-provided URLs.
"""

import logging
from typing import Dict, Optional
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class URLFetcher:
    """Safely retrieves public web pages and returns cleaned text and metadata."""

    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36 DeadlineGuardian/1.0"
        )
    }

    @classmethod
    def fetch(cls, url: str, timeout: int = 10) -> Dict[str, Optional[str]]:
        """
        Fetch HTML from URL and extract readable title, domain, and body text.

        Returns:
            Dict containing:
              - 'url': original or normalized URL
              - 'domain': host domain
              - 'title': extracted page title
              - 'text': cleaned plain text content
              - 'error': error message if failed, else None
        """
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        domain = urlparse(url).netloc

        try:
            response = requests.get(
                url,
                headers=cls.DEFAULT_HEADERS,
                timeout=timeout,
                allow_redirects=True,
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Remove unwanted script, style, and navigation noise
            for element in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                element.decompose()

            title = soup.title.string.strip() if soup.title and soup.title.string else domain

            # Get main text lines
            lines = (line.strip() for line in soup.get_text().splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = "\n".join(chunk for chunk in chunks if chunk)

            # Cap extracted text length to avoid memory bloat
            truncated_text = clean_text[:12000]

            return {
                "url": url,
                "domain": domain,
                "title": title,
                "text": truncated_text,
                "error": None,
            }

        except requests.exceptions.RequestException as e:
            logger.warning("Failed to fetch URL %s: %s", url, e)
            return {
                "url": url,
                "domain": domain,
                "title": None,
                "text": None,
                "error": f"Failed to retrieve URL ({type(e).__name__}): {e}",
            }
