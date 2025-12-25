from __future__ import annotations

from typing import ClassVar

import httpx
from loguru import logger


class HTTPMatchClient:
    """HTTP client for fetching match pages from csvp.cz."""

    BASE_URL: ClassVar[str] = "https://www.csvp.cz"
    DEFAULT_TIMEOUT: ClassVar[float] = 30.0
    DEFAULT_USER_AGENT: ClassVar[str] = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    def __init__(
        self,
        base_url: str = BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        user_agent: str = DEFAULT_USER_AGENT,
    ):
        """Initialize the HTTP client.

        Args:
            base_url: The base URL to use for the client.
            timeout: The timeout to use for the client.
            user_agent: The user agent to use for the client.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.user_agent = user_agent
        self._client: httpx.Client | None = None

    def __enter__(self):
        """Context manager entry."""
        self._client = httpx.Client(
            timeout=self.timeout,
            headers={"User-Agent": self.user_agent},
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._client:
            self._client.close()
            self._client = None

    def fetch_match(self, match_id: int) -> str:
        """Fetch HTML content for a match.

        Args:
            match_id: Match ID from URL

        Returns:
            HTML content as string

        Raises:
            httpx.HTTPError: If HTTP request fails
            httpx.TimeoutException: If request times out
            ValueError: If match_id is invalid
        """
        if match_id <= 0:
            logger.error(f"match_id must be positive, got {match_id}")
            raise ValueError(f"match_id must be positive, got {match_id}")

        if not self._client:
            logger.error("MatchClient must be used as context manager")
            raise RuntimeError("MatchClient must be used as context manager")

        url = f"{self.base_url}/zapas/{match_id}"
        response = self._client.get(url)
        response.raise_for_status()
        return response.text
