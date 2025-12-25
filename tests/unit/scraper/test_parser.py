from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from cze_wp_scraper.models.match import MatchModel
from cze_wp_scraper.scraper.parser import MatchInfoParser
from cze_wp_scraper.utils.exceptions import MatchParsingError

# Get the path to the example HTML fixture
FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures"
EXAMPLE_HTML_PATH = FIXTURES_DIR / "example_match.html"


@pytest.fixture
def example_html() -> str:
    """Load example HTML from fixture file."""
    return EXAMPLE_HTML_PATH.read_text(encoding="utf-8")


class TestMatchInfoParser:
    """Test cases for MatchInfoParser."""

    def test_parse_match_success(self, example_html: str) -> None:
        """Test successful parsing of match data."""
        result = MatchInfoParser.parse_match(example_html, game_id=2425)

        assert isinstance(result, MatchModel)
        assert result.game_id == 2425
        assert result.home_team == "UKVP Stepp Praha"
        assert result.away_team == "SK UP Olomouc"
        # Note: Date format in HTML has spaces: "21. 12. 2025 - 11:00"
        # The validator converts it, so we check the datetime object directly
        assert result.match_date.year == 2025
        assert result.match_date.month == 12
        assert result.match_date.day == 21
        assert result.match_date.hour == 11
        assert result.match_date.minute == 0
        assert result.league == "1. liga mužů - základní část"
        assert result.home_score == 33
        assert result.away_score == 5
        assert result.winner == "H"

    def test_extract_league_and_date(self, example_html: str) -> None:
        """Test extraction of league and date."""

        soup = BeautifulSoup(example_html, "lxml")
        league, match_date = MatchInfoParser._extract_league_and_date(soup)

        assert league == "1. liga mužů - základní část"
        assert match_date == "21.12.2025 11:00:00"

    def test_extract_league_and_date_missing_comma(self) -> None:
        """Test extraction when comma is missing."""
        html = """
        <div class="head match-detail">
            <div class="col-12 text-center">
                21. 12. 2025 - 11:00
                <div class="place">Location</div>
            </div>
        </div>
        """

        soup = BeautifulSoup(html, "lxml")
        with pytest.raises(MatchParsingError):
            MatchInfoParser._extract_league_and_date(soup)

    def test_extract_league_and_date_no_place(self) -> None:
        """Test extraction when place div is missing."""
        html = """
        <div class="head match-detail blue br-btm">
            <div class="col-12 text-center">
                21. 12. 2025 - 11:00, 1. liga mužů
            </div>
        </div>
        """

        soup = BeautifulSoup(html, "lxml")
        league, match_date = MatchInfoParser._extract_league_and_date(soup)

        assert league == "1. liga mužů"
        assert match_date == "21.12.2025 11:00:00"

    def test_extract_teams(self, example_html: str) -> None:
        """Test extraction of team names."""

        soup = BeautifulSoup(example_html, "lxml")
        home_team, away_team = MatchInfoParser._extract_teams(soup)

        assert home_team == "UKVP Stepp Praha"
        assert away_team == "SK UP Olomouc"

    def test_extract_teams_filters_quarters(self) -> None:
        """Test that quarter headers are filtered out."""
        html = """
        <div class="whole">
            <div class="row">
                <div class="col-12">
                    <h3 class="tab-title grey">Home Team</h3>
                </div>
                <div class="col-12">
                    <h3 class="tab-title grey text-right">Away Team</h3>
                </div>
                <div class="col-12">
                    <h3 class="tab-title grey">1. čtvrtina</h3>
                </div>
                <div class="col-12">
                    <h3 class="tab-title grey">2. čtvrtina</h3>
                </div>
            </div>
        </div>
        """

        soup = BeautifulSoup(html, "lxml")
        home_team, away_team = MatchInfoParser._extract_teams(soup)

        assert home_team == "Home Team"
        assert away_team == "Away Team"

    def test_extract_teams_missing_whole_div(self) -> None:
        """Test extraction when whole div is missing."""
        html = "<html><body></body></html>"

        soup = BeautifulSoup(html, "lxml")
        with pytest.raises(MatchParsingError):
            MatchInfoParser._extract_teams(soup)

    def test_extract_teams_only_one_team(self) -> None:
        """Test extraction when only one team is present."""
        html = """
        <div class="whole">
            <div class="row">
                <div class="col-12">
                    <h3 class="tab-title grey">Home Team</h3>
                </div>
            </div>
        </div>
        """

        soup = BeautifulSoup(html, "lxml")
        home_team, away_team = MatchInfoParser._extract_teams(soup)

        assert home_team == "Home Team"
        assert away_team == ""

    def test_extract_score(self, example_html: str) -> None:
        """Test extraction of score."""

        soup = BeautifulSoup(example_html, "lxml")
        home_score, away_score = MatchInfoParser._extract_score(soup)

        assert home_score == 33
        assert away_score == 5

    def test_extract_score_different_format(self) -> None:
        """Test extraction with different score format."""
        html = """
        <div class="col-12 col-md-12 col-lg-12 col-xl-2 score mb-4">
            15:12
            <div>(5:3, 4:2, 3:4, 3:3)</div>
            <div class="state">Ukončené utkání</div>
        </div>
        """

        soup = BeautifulSoup(html, "lxml")
        home_score, away_score = MatchInfoParser._extract_score(soup)

        assert home_score == 15
        assert away_score == 12

    def test_extract_score_with_whitespace(self) -> None:
        """Test extraction with extra whitespace."""
        html = """
        <div class="col-12 col-md-12 col-lg-12 col-xl-2 score mb-4">
            10 : 8
            <div class="state">Ukončené utkání</div>
        </div>
        """

        soup = BeautifulSoup(html, "lxml")
        home_score, away_score = MatchInfoParser._extract_score(soup)

        assert home_score == 10
        assert away_score == 8

    def test_extract_score_missing_colon(self) -> None:
        """Test extraction when score format is invalid."""
        html = """
        <div class="col-12 col-md-12 col-lg-12 col-xl-2 score mb-4">
            Invalid Score
            <div class="state">Ukončené utkání</div>
        </div>
        """

        soup = BeautifulSoup(html, "lxml")
        with pytest.raises(MatchParsingError):
            MatchInfoParser._extract_score(soup)

    def test_extract_score_missing_div(self) -> None:
        """Test extraction when score div is missing."""
        html = "<html><body></body></html>"

        soup = BeautifulSoup(html, "lxml")
        with pytest.raises(AttributeError):
            MatchInfoParser._extract_score(soup)

    def test_determine_winner_home_wins(self) -> None:
        """Test winner determination when home team wins."""
        assert MatchInfoParser._determine_winner(10, 5) == "H"
        assert MatchInfoParser._determine_winner(1, 0) == "H"

    def test_determine_winner_away_wins(self) -> None:
        """Test winner determination when away team wins."""
        assert MatchInfoParser._determine_winner(5, 10) == "A"
        assert MatchInfoParser._determine_winner(0, 1) == "A"

    def test_determine_winner_draw(self) -> None:
        """Test winner determination when it's a draw."""
        assert MatchInfoParser._determine_winner(5, 5) == "D"
        assert MatchInfoParser._determine_winner(0, 0) == "D"
        assert MatchInfoParser._determine_winner(10, 10) == "D"

    def test_parse_match_home_wins(self, example_html: str) -> None:
        """Test parsing when home team wins."""
        result = MatchInfoParser.parse_match(example_html, game_id=2425)

        assert result is not None
        assert result.winner == "H"
        assert result.home_score > result.away_score

    def test_parse_match_away_wins(self) -> None:
        """Test parsing when away team wins."""
        html = """
        <html>
        <body>
            <div class="head match-detail blue br-btm">
                <div class="col-12 text-center">
                    21. 12. 2025 - 11:00, 1. liga mužů
                    <div class="place">Location</div>
                </div>
                <div class="col-12 col-md-12 col-lg-12 col-xl-2 score mb-4">
                    5:10
                    <div class="state">Ukončené utkání</div>
                </div>
            </div>
            <div class="whole">
                <div class="row">
                    <div class="col-12">
                        <h3 class="tab-title grey">Home Team</h3>
                    </div>
                    <div class="col-12">
                        <h3 class="tab-title grey">Away Team</h3>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        result = MatchInfoParser.parse_match(html, game_id=123)

        assert result is not None
        assert result.winner == "A"
        assert result.home_score < result.away_score

    def test_parse_match_draw(self) -> None:
        """Test parsing when it's a draw."""
        html = """
        <html>
        <body>
            <div class="head match-detail blue br-btm">
                <div class="col-12 text-center">
                    21. 12. 2025 - 11:00, 1. liga mužů
                    <div class="place">Location</div>
                </div>
                <div class="col-12 col-md-12 col-lg-12 col-xl-2 score mb-4">
                    10:10
                    <div class="state">Ukončené utkání</div>
                </div>
            </div>
            <div class="whole">
                <div class="row">
                    <div class="col-12">
                        <h3 class="tab-title grey">Home Team</h3>
                    </div>
                    <div class="col-12">
                        <h3 class="tab-title grey">Away Team</h3>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        result = MatchInfoParser.parse_match(html, game_id=123)

        assert result is not None
        assert result.winner == "D"
        assert result.home_score == result.away_score

    def test_parse_match_different_game_id(self, example_html: str) -> None:
        """Test parsing with different game_id."""
        result = MatchInfoParser.parse_match(example_html, game_id=9999)

        assert result is not None
        assert result.game_id == 9999
        # Other fields should be the same
        assert result.home_team == "UKVP Stepp Praha"

    def test_parse_match_empty_html(self) -> None:
        """Test parsing with empty HTML."""
        html = "<html><body></body></html>"
        with pytest.raises(MatchParsingError):
            MatchInfoParser.parse_match(html, game_id=123)

    def test_parse_match_malformed_html(self) -> None:
        """Test parsing with malformed HTML."""
        html = "<div>Incomplete HTML"
        # BeautifulSoup should handle this, but extraction might fail
        with pytest.raises(MatchParsingError):
            MatchInfoParser.parse_match(html, game_id=123)

    def test_parse_match_date_validation(self, example_html: str) -> None:
        """Test that match_date is properly converted to datetime."""

        result = MatchInfoParser.parse_match(example_html, game_id=2425)

        assert result is not None

        assert isinstance(result.match_date, datetime)
        assert hasattr(result.match_date, "strftime")

    def test_parse_match_all_fields_present(self, example_html: str) -> None:
        """Test that all required fields are extracted."""
        result = MatchInfoParser.parse_match(example_html, game_id=2425)

        assert result is not None
        assert result.game_id is not None
        assert result.home_team is not None and result.home_team != ""
        assert result.away_team is not None and result.away_team != ""
        assert result.match_date is not None
        assert result.league is not None
        assert isinstance(result.home_score, int)
        assert isinstance(result.away_score, int)
        assert result.winner in ("H", "A", "D")
