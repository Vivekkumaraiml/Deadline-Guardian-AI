"""
Configuration management for Deadline Guardian AI.
Loads settings from environment variables or a local .env file.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load local .env if present
load_dotenv()


class Settings:
    # Mode flags
    MOCK_SEARCH_MODE: bool = os.getenv("MOCK_SEARCH_MODE", "true").lower() in ("true", "1", "yes")

    # Search credentials
    TAVILY_API_KEY: Optional[str] = os.getenv("TAVILY_API_KEY", "").strip() or None
    SERPER_API_KEY: Optional[str] = os.getenv("SERPER_API_KEY", "").strip() or None

    # uAgent & Agentverse settings
    AGENT_NAME: str = os.getenv("AGENT_NAME", "deadline_guardian_ai")
    AGENT_SEED: str = os.getenv("AGENT_SEED", "deadline_guardian_ai_fetchathon_2026_secret_seed_phrase")
    AGENT_MAILBOX: bool = os.getenv("AGENT_MAILBOX", "true").lower() in ("true", "1", "yes")
    AGENTVERSE_MAILBOX_KEY: Optional[str] = os.getenv("AGENTVERSE_MAILBOX_KEY", "").strip() or None
    AGENT_PORT: int = int(os.getenv("AGENT_PORT", "8000"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def is_live_search_available(cls) -> bool:
        """Returns True if any live search API key is configured."""
        return bool(cls.TAVILY_API_KEY or cls.SERPER_API_KEY)


settings = Settings()
