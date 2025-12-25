from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from bs4 import BeautifulSoup
from loguru import logger

from cze_wp_scraper.models.match import MatchModel
from cze_wp_scraper.utils.constants import Constants
from cze_wp_scraper.utils.exceptions import MatchParsingError


class MatchInfoParser:
    """Parser for parsing match data from HTML."""

    DATE_LEAGUE_DIV_CLASS: ClassVar[str] = "head match-detail blue br-btm"
    DATE_LEAGUE_TEXT_CLASS: ClassVar[str] = "col-12 text-center"
    TEAM_HEADERS_CLASS: ClassVar[str] = "whole"
    SCORE_DIV_CLASS: ClassVar[str] = "col-12 col-md-12 col-lg-12 col-xl-2 score mb-4"

    QUARTER_HEADER_TEXT: ClassVar[str] = "čtvrtina"
    INPUT_DATE_FORMAT: ClassVar[str] = "%d. %m. %Y - %H:%M"
    MATCH_FINISHED_TEXT: ClassVar[str] = "Ukončené utkání"

    @classmethod
    def _extract_league_and_date(cls, soup: BeautifulSoup) -> tuple[str, str]:
        """Extract league and date from HTML."""
        try:
            date_league_div = soup.find("div", class_=cls.DATE_LEAGUE_DIV_CLASS)
            date_league_div = date_league_div.find("div", class_=cls.DATE_LEAGUE_TEXT_CLASS)

            date_league_text = date_league_div.get_text(strip=False)
            date_league_text = date_league_text.split("\n")[1].strip()

            res = date_league_text.split(",")
            league = res[1].strip()
            match_date_str = res[0].strip()

            return league, datetime.strptime(match_date_str, cls.INPUT_DATE_FORMAT).strftime(
                Constants.OUTPUT_DATE_FORMAT
            )
        except (AttributeError, ValueError) as e:
            logger.error(f"Failed to extract league and date: {e}")
            raise MatchParsingError(f"Failed to extract league and date: {e}") from e

    @classmethod
    def _extract_teams(cls, soup: BeautifulSoup) -> tuple[str, str]:
        """Extract teams from HTML."""
        try:
            whole_div = soup.find("div", class_=cls.TEAM_HEADERS_CLASS)
            team_headers = whole_div.find_all("h3")
            # Filter out quarter headers (contain "čtvrtina")
            team_names = [
                h3.get_text(strip=True) for h3 in team_headers if cls.QUARTER_HEADER_TEXT not in h3.get_text(strip=True)
            ]
            home_team = team_names[0] if len(team_names) > 0 else ""
            away_team = team_names[1] if len(team_names) > 1 else ""
        except AttributeError as e:
            logger.error("Failed to extract teams")
            raise MatchParsingError("Failed to extract teams") from e
        return home_team, away_team

    @classmethod
    def _extract_score(cls, soup: BeautifulSoup) -> tuple[int, int] | tuple[None, None]:
        """Extract score from HTML."""
        try:
            score_div = soup.find("div", class_=cls.SCORE_DIV_CLASS)
            score_text = score_div.get_text(strip=False)
            if cls.MATCH_FINISHED_TEXT not in score_text:
                logger.info("Match is not finished yet. Skipping match.")
                return None, None
            score_text = score_text.split("\n")[1].strip()

            home_score_str, away_score_str = score_text.split(":")
            home_score = int(home_score_str.strip())
            away_score = int(away_score_str.strip())

        except ValueError as e:
            logger.error(f"Failed to extract score: {e}")
            raise MatchParsingError(f"Failed to extract score, invalid score format: {e}") from e
        return home_score, away_score

    @staticmethod
    def _determine_winner(home_score: int, away_score: int) -> str:
        """Determine winner from score."""
        if home_score > away_score:
            return "H"
        if away_score > home_score:
            return "A"
        return "D"

    @classmethod
    def parse_match(cls, html: str, game_id: int) -> MatchModel | None:
        """Parse match data from HTML."""
        soup = BeautifulSoup(html, "lxml")

        # 1. Extract date and league
        league, match_date = cls._extract_league_and_date(soup)

        # 2. Extract teams from div.whole
        home_team, away_team = cls._extract_teams(soup)

        # 3. Extract score
        home_score, away_score = cls._extract_score(soup)
        if not home_score or not away_score:
            return None

        # 4. Determine winner
        winner = cls._determine_winner(home_score, away_score)

        return MatchModel(
            game_id=game_id,
            home_team=home_team,
            away_team=away_team,
            match_date=match_date,
            league=league,
            home_score=home_score,
            away_score=away_score,
            winner=winner,
        )
