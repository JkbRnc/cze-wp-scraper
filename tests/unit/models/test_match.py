from __future__ import annotations

from datetime import datetime

from cze_wp_scraper.models.match import MatchModel
from cze_wp_scraper.utils.constants import Constants


class TestMatchModel:
    """Test cases for MatchModel."""

    def test_validate_match_date(self) -> None:
        """Test validate_match_date method."""
        match_date = "21.12.2025 11:00:00"
        match_model = MatchModel(
            game_id=1,
            home_team="Home Team",
            away_team="Away Team",
            match_date=match_date,
            league="League",
            home_score=1,
            away_score=2,
            winner="H",
        )
        assert match_model.match_date == datetime.strptime(match_date, Constants.OUTPUT_DATE_FORMAT)
        assert match_model.game_id == 1
        assert match_model.home_team == "Home Team"
        assert match_model.away_team == "Away Team"
        assert match_model.league == "League"
        assert match_model.home_score == 1
        assert match_model.away_score == 2
        assert match_model.winner == "H"

    def test_validate_match_date_datetime(self) -> None:
        """Test validate_match_date method."""
        match_date = datetime(2025, 12, 21, 11, 0, 0)
        match_model = MatchModel(
            game_id=1,
            home_team="Home Team",
            away_team="Away Team",
            match_date=match_date,
            league="League",
            home_score=1,
            away_score=2,
            winner="H",
        )
        assert match_model.match_date == match_date
        assert match_model.game_id == 1
        assert match_model.home_team == "Home Team"
        assert match_model.away_team == "Away Team"
        assert match_model.league == "League"
        assert match_model.home_score == 1
        assert match_model.away_score == 2
        assert match_model.winner == "H"
