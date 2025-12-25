from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
from loguru import logger

from cze_wp_scraper.scraper.client import HTTPMatchClient
from cze_wp_scraper.scraper.parser import MatchInfoParser
from cze_wp_scraper.utils.exceptions import MatchParsingError

if TYPE_CHECKING:
    from cze_wp_scraper.models.match import MatchModel


class MatchScraper:
    """Scraper for fetching and parsing multiple match data from csvp.cz."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
        user_agent: str | None = None,
    ):
        """Initialize the scraper.

        Args:
            base_url: Optional base URL for the HTTP client. Uses default if None.
            timeout: Optional timeout for the HTTP client. Uses default if None.
            user_agent: Optional user agent for the HTTP client. Uses default if None.
        """
        self.base_url = base_url
        self.timeout = timeout
        self.user_agent = user_agent

    def _get_client_kwargs(self) -> dict[str, str | float]:
        """Get client initialization kwargs from instance attributes."""
        client_kwargs: dict[str, str | float] = {}
        if self.base_url is not None:
            client_kwargs["base_url"] = self.base_url
        if self.timeout is not None:
            client_kwargs["timeout"] = self.timeout
        if self.user_agent is not None:
            client_kwargs["user_agent"] = self.user_agent
        return client_kwargs

    @staticmethod
    def _scrape_single_match(client: HTTPMatchClient, game_id: int) -> MatchModel | None:
        """Scrape a single match.

        Args:
            client: HTTP client instance.
            game_id: Game ID to scrape.

        Returns:
            MatchModel if successful, None if failed.
        """
        try:
            html = client.fetch_match(game_id)
            return MatchInfoParser.parse_match(html, game_id)
        except MatchParsingError as e:
            logger.error(f"Failed to scrape match {game_id}: {e}")
            return None

    @staticmethod
    def _matches_to_dataframe(matches: list[MatchModel]) -> pd.DataFrame:
        """Convert list of MatchModel to pandas DataFrame.

        Args:
            matches: List of MatchModel objects.

        Returns:
            pandas DataFrame with match data.
        """
        if not matches:
            # Return empty DataFrame with correct columns if no matches
            return pd.DataFrame(
                columns=[
                    "game_id",
                    "home_team",
                    "away_team",
                    "match_date",
                    "league",
                    "home_score",
                    "away_score",
                    "winner",
                ]
            )

        # Convert MatchModel objects to dictionaries
        match_dicts = [match.model_dump() for match in matches]

        # Create DataFrame with correct column order
        column_order = [
            "game_id",
            "home_team",
            "away_team",
            "match_date",
            "league",
            "home_score",
            "away_score",
            "winner",
        ]
        return pd.DataFrame(match_dicts)[column_order]

    def scrape_matches(self, game_ids: list[int]) -> pd.DataFrame:
        """Scrape match data for a list of game IDs.

        Args:
            game_ids: List of game IDs to scrape.

        Returns:
            pandas DataFrame with columns matching MatchModel fields:
            - game_id
            - home_team
            - away_team
            - match_date
            - league
            - home_score
            - away_score
            - winner

        Note:
            Games that fail to fetch or parse are skipped (not included in the result).
        """
        matches: list[MatchModel] = []

        with HTTPMatchClient(**self._get_client_kwargs()) as client:  # type: ignore[arg-type]
            for game_id in game_ids:
                match_data = self._scrape_single_match(client, game_id)
                if match_data is not None:
                    logger.info(f"Scraped match {game_id} successfully")
                    matches.append(match_data)

        return self._matches_to_dataframe(matches)
