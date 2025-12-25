from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pandas as pd
import pytest

from cze_wp_scraper.models.match import MatchModel
from cze_wp_scraper.scraper.parser import MatchInfoParser
from cze_wp_scraper.scraper.scraper import MatchScraper
from cze_wp_scraper.utils.exceptions import MatchParsingError

# Get the path to the example HTML fixture
FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures"
EXAMPLE_HTML_PATH = FIXTURES_DIR / "example_match.html"


@pytest.fixture
def example_html() -> str:
    """Load example HTML from fixture file."""
    return EXAMPLE_HTML_PATH.read_text(encoding="utf-8")


@pytest.fixture
def example_match_model() -> MatchModel:
    """Create a sample MatchModel for testing."""
    return MatchModel(
        game_id=2425,
        home_team="UKVP Stepp Praha",
        away_team="SK UP Olomouc",
        match_date="21.12.2025 11:00:00",
        league="1. liga mužů - základní část",
        home_score=33,
        away_score=5,
        winner="H",
    )


@pytest.fixture
def mock_httpx_client(example_html: str) -> MagicMock:
    """Create a mocked httpx.Client that returns example HTML."""
    mock_client = MagicMock(spec=httpx.Client, fetch_match=MagicMock(return_value=example_html))
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.text = example_html
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_client.get.return_value = mock_response
    return mock_client


class TestMatchScraper:
    """Test cases for MatchScraper."""

    def test_init_defaults(self) -> None:
        """Test MatchScraper initialization with default values."""
        scraper = MatchScraper()
        assert scraper.base_url is None
        assert scraper.timeout is None
        assert scraper.user_agent is None

    def test_init_custom_values(self) -> None:
        """Test MatchScraper initialization with custom values."""
        scraper = MatchScraper(
            base_url="https://example.com",
            timeout=60.0,
            user_agent="Custom Agent",
        )
        assert scraper.base_url == "https://example.com"
        assert scraper.timeout == 60.0
        assert scraper.user_agent == "Custom Agent"

    def test_get_client_kwargs_all_none(self) -> None:
        """Test _get_client_kwargs when all attributes are None."""
        scraper = MatchScraper()
        kwargs = scraper._get_client_kwargs()
        assert kwargs == {}

    def test_get_client_kwargs_all_set(self) -> None:
        """Test _get_client_kwargs when all attributes are set."""
        scraper = MatchScraper(
            base_url="https://example.com",
            timeout=60.0,
            user_agent="Custom Agent",
        )
        kwargs = scraper._get_client_kwargs()
        assert kwargs == {
            "base_url": "https://example.com",
            "timeout": 60.0,
            "user_agent": "Custom Agent",
        }

    def test_get_client_kwargs_partial(self) -> None:
        """Test _get_client_kwargs when only some attributes are set."""
        scraper = MatchScraper(timeout=45.0)
        kwargs = scraper._get_client_kwargs()
        assert kwargs == {"timeout": 45.0}

    def test_scrape_single_match_success(self, mock_httpx_client: MagicMock, example_match_model: MatchModel) -> None:
        """Test _scrape_single_match with successful fetch and parse."""
        with patch.object(MatchInfoParser, "parse_match", return_value=example_match_model):
            result = MatchScraper._scrape_single_match(mock_httpx_client, game_id=2425)

            assert result is not None
            assert isinstance(result, MatchModel)
            assert result.game_id == 2425
            mock_httpx_client.fetch_match.assert_called_once_with(2425)
            MatchInfoParser.parse_match.assert_called_once()

    def test_scrape_single_match_fetch_error(self, mock_httpx_client: MagicMock) -> None:
        """Test _scrape_single_match when fetch fails."""
        mock_httpx_client.fetch_match.side_effect = httpx.HTTPStatusError(
            "404 Not Found",
            request=MagicMock(),
            response=MagicMock(),
        )

        with pytest.raises(httpx.HTTPStatusError):
            MatchScraper._scrape_single_match(mock_httpx_client, game_id=9999)

    def test_scrape_single_match_parse_error(self, mock_httpx_client: MagicMock) -> None:
        """Test _scrape_single_match when parse fails."""
        with patch.object(MatchInfoParser, "parse_match", side_effect=MatchParsingError("Parse error")):
            result = MatchScraper._scrape_single_match(mock_httpx_client, game_id=2425)

            assert result is None

    def test_matches_to_dataframe_empty(self) -> None:
        """Test _matches_to_dataframe with empty list."""
        df = MatchScraper._matches_to_dataframe([])

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        expected_columns = [
            "game_id",
            "home_team",
            "away_team",
            "match_date",
            "league",
            "home_score",
            "away_score",
            "winner",
        ]
        assert list(df.columns) == expected_columns

    def test_matches_to_dataframe_single(self, example_match_model: MatchModel) -> None:
        """Test _matches_to_dataframe with single match."""
        df = MatchScraper._matches_to_dataframe([example_match_model])

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df.iloc[0]["game_id"] == 2425
        assert df.iloc[0]["home_team"] == "UKVP Stepp Praha"
        assert df.iloc[0]["away_team"] == "SK UP Olomouc"
        assert df.iloc[0]["home_score"] == 33
        assert df.iloc[0]["away_score"] == 5
        assert df.iloc[0]["winner"] == "H"

    def test_matches_to_dataframe_multiple(self, example_match_model: MatchModel) -> None:
        """Test _matches_to_dataframe with multiple matches."""
        match2 = MatchModel(
            game_id=2424,
            home_team="Team A",
            away_team="Team B",
            match_date="20.12.2025 10:00:00",
            league="1. liga mužů",
            home_score=10,
            away_score=8,
            winner="H",
        )
        df = MatchScraper._matches_to_dataframe([example_match_model, match2])

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df["game_id"]) == [2425, 2424]
        assert list(df["home_team"]) == ["UKVP Stepp Praha", "Team A"]

    def test_matches_to_dataframe_column_order(self, example_match_model: MatchModel) -> None:
        """Test that _matches_to_dataframe returns columns in correct order."""
        df = MatchScraper._matches_to_dataframe([example_match_model])

        expected_order = [
            "game_id",
            "home_team",
            "away_team",
            "match_date",
            "league",
            "home_score",
            "away_score",
            "winner",
        ]
        assert list(df.columns) == expected_order

    def test_scrape_matches_success(
        self, example_html: str, example_match_model: MatchModel, mock_httpx_client: MagicMock
    ) -> None:
        """Test scrape_matches with successful scraping."""
        with (
            patch("cze_wp_scraper.scraper.scraper.HTTPMatchClient") as mock_client_class,
            patch.object(MatchInfoParser, "parse_match", return_value=example_match_model),
        ):
            mock_client_class.return_value.__enter__.return_value = mock_httpx_client
            mock_httpx_client.fetch_match.return_value = example_html

            scraper = MatchScraper()
            game_ids = [2425]
            df = scraper.scrape_matches(game_ids)

            assert isinstance(df, pd.DataFrame)
            assert len(df) == 1
            assert df.iloc[0]["game_id"] == 2425

    def test_scrape_matches_multiple_success(
        self, example_html: str, example_match_model: MatchModel, mock_httpx_client: MagicMock
    ) -> None:
        """Test scrape_matches with multiple successful matches."""
        match2 = MatchModel(
            game_id=2424,
            home_team="Team A",
            away_team="Team B",
            match_date="20.12.2025 10:00:00",
            league="1. liga mužů",
            home_score=10,
            away_score=8,
            winner="H",
        )

        def parse_side_effect(html: str, game_id: int) -> MatchModel:
            if game_id == 2425:
                return example_match_model
            return match2

        with (
            patch("cze_wp_scraper.scraper.scraper.HTTPMatchClient") as mock_client_class,
            patch.object(MatchInfoParser, "parse_match", side_effect=parse_side_effect),
        ):
            mock_client_class.return_value.__enter__.return_value = mock_httpx_client
            mock_httpx_client.fetch_match.return_value = example_html

            scraper = MatchScraper()
            game_ids = [2425, 2424]
            df = scraper.scrape_matches(game_ids)

            assert isinstance(df, pd.DataFrame)
            assert len(df) == 2
            assert list(df["game_id"]) == [2425, 2424]

    def test_scrape_matches_partial_failure(
        self, example_html: str, example_match_model: MatchModel, mock_httpx_client: MagicMock
    ) -> None:
        """Test scrape_matches when some matches fail."""

        def fetch_side_effect(game_id: int) -> str:
            if game_id == 2425:
                return example_html
            raise httpx.HTTPStatusError("404 Not Found", request=MagicMock(), response=MagicMock())

        with (
            patch("cze_wp_scraper.scraper.scraper.HTTPMatchClient") as mock_client_class,
            patch.object(MatchInfoParser, "parse_match", return_value=example_match_model),
        ):
            mock_client_class.return_value.__enter__.return_value = mock_httpx_client
            mock_httpx_client.fetch_match.side_effect = fetch_side_effect

            scraper = MatchScraper()
            game_ids = [2425, 9999]  # 9999 will fail
            with pytest.raises(httpx.HTTPStatusError):
                df = scraper.scrape_matches(game_ids)

                assert isinstance(df, pd.DataFrame)
                assert len(df) == 1  # Only successful match
                assert df.iloc[0]["game_id"] == 2425

    def test_scrape_matches_all_fail(self, mock_httpx_client: MagicMock) -> None:
        """Test scrape_matches when all matches fail."""
        mock_httpx_client.fetch_match.side_effect = httpx.HTTPStatusError(
            "404 Not Found",
            request=MagicMock(),
            response=MagicMock(),
        )

        with (
            patch("cze_wp_scraper.scraper.scraper.HTTPMatchClient") as mock_client_class,
            pytest.raises(httpx.HTTPStatusError),
        ):
            mock_client_class.return_value.__enter__.return_value = mock_httpx_client

            scraper = MatchScraper()
            game_ids = [9999, 9998]
            scraper.scrape_matches(game_ids)

    def test_scrape_matches_empty_list(self) -> None:
        """Test scrape_matches with empty game_ids list."""
        with patch("cze_wp_scraper.scraper.scraper.HTTPMatchClient"):
            scraper = MatchScraper()
            df = scraper.scrape_matches([])

            assert isinstance(df, pd.DataFrame)
            assert len(df) == 0
            expected_columns = [
                "game_id",
                "home_team",
                "away_team",
                "match_date",
                "league",
                "home_score",
                "away_score",
                "winner",
            ]
            assert list(df.columns) == expected_columns

    def test_scrape_matches_custom_client_config(
        self, example_html: str, example_match_model: MatchModel, mock_httpx_client: MagicMock
    ) -> None:
        """Test scrape_matches passes custom client configuration."""
        with (
            patch("cze_wp_scraper.scraper.scraper.HTTPMatchClient") as mock_client_class,
            patch.object(MatchInfoParser, "parse_match", return_value=example_match_model),
        ):
            mock_client_class.return_value.__enter__.return_value = mock_httpx_client
            mock_httpx_client.fetch_match.return_value = example_html

            scraper = MatchScraper(
                base_url="https://custom.example.com",
                timeout=60.0,
                user_agent="Custom Agent",
            )
            game_ids = [2425]
            scraper.scrape_matches(game_ids)

            # Verify HTTPMatchClient was called with custom kwargs
            mock_client_class.assert_called_once()
            call_kwargs = mock_client_class.call_args[1]
            assert call_kwargs["base_url"] == "https://custom.example.com"
            assert call_kwargs["timeout"] == 60.0
            assert call_kwargs["user_agent"] == "Custom Agent"

    def test_scrape_matches_parse_error_skipped(self, example_html: str, mock_httpx_client: MagicMock) -> None:
        """Test that matches with parse errors are skipped."""
        with (
            patch("cze_wp_scraper.scraper.scraper.HTTPMatchClient") as mock_client_class,
            patch.object(MatchInfoParser, "parse_match", side_effect=ValueError("Parse error")),
            pytest.raises(ValueError),
        ):
            mock_client_class.return_value.__enter__.return_value = mock_httpx_client
            mock_httpx_client.fetch_match.return_value = example_html

            scraper = MatchScraper()
            game_ids = [2425]

            df = scraper.scrape_matches(game_ids)

            assert isinstance(df, pd.DataFrame)
            assert len(df) == 0  # Failed match is skipped
