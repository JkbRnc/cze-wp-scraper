from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

from cze_wp_scraper.scraper.client import HTTPMatchClient

# Get the path to the example HTML fixture
FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures"
EXAMPLE_HTML_PATH = FIXTURES_DIR / "example_match.html"


@pytest.fixture
def example_html() -> str:
    """Load example HTML from fixture file."""
    return EXAMPLE_HTML_PATH.read_text(encoding="utf-8")


@pytest.fixture
def mock_httpx_client(example_html: str) -> MagicMock:
    """Create a mocked httpx.Client that returns example HTML."""
    mock_client = MagicMock(spec=httpx.Client)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.text = example_html
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_client.get.return_value = mock_response
    return mock_client


class TestMatchClient:
    """Test cases for MatchClient."""

    def test_init_defaults(self) -> None:
        """Test MatchClient initialization with default values."""
        client = HTTPMatchClient()
        assert client.base_url == "https://www.csvp.cz"
        assert client.timeout == 30.0
        assert client._client is None

    def test_init_custom_values(self) -> None:
        """Test MatchClient initialization with custom values."""
        client = HTTPMatchClient(
            base_url="https://example.com",
            timeout=60.0,
            user_agent="Custom Agent",
        )
        assert client.base_url == "https://example.com"
        assert client.timeout == 60.0
        assert client.user_agent == "Custom Agent"

    def test_init_strips_trailing_slash(self) -> None:
        """Test that base_url trailing slash is stripped."""
        client = HTTPMatchClient(base_url="https://example.com/")
        assert client.base_url == "https://example.com"

    def test_context_manager_creates_client(self) -> None:
        """Test that context manager creates httpx.Client."""
        with patch("cze_wp_scraper.scraper.client.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            with HTTPMatchClient() as client:
                assert client._client is not None
                mock_client_class.assert_called_once()
                assert mock_client_class.call_args[1]["timeout"] == 30.0
                assert "User-Agent" in mock_client_class.call_args[1]["headers"]

    def test_context_manager_closes_client(self) -> None:
        """Test that context manager closes httpx.Client on exit."""
        with patch("cze_wp_scraper.scraper.client.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            with HTTPMatchClient() as client:
                pass

            mock_client.close.assert_called_once()
            assert client._client is None

    def test_context_manager_closes_on_empty_client(self) -> None:
        """Test that context manager closes httpx.Client on exit when client is None."""
        with patch("cze_wp_scraper.scraper.client.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            with HTTPMatchClient() as client:
                client._client = None

            mock_client.close.assert_not_called()

    def test_fetch_match_success(self, example_html: str, mock_httpx_client: MagicMock) -> None:
        """Test successful match fetch."""
        with (
            patch("cze_wp_scraper.scraper.client.httpx.Client", return_value=mock_httpx_client),
            HTTPMatchClient() as client,
        ):
            result = client.fetch_match(2425)

            assert result == example_html
            mock_httpx_client.get.assert_called_once_with("https://www.csvp.cz/zapas/2425")
            mock_httpx_client.get.return_value.raise_for_status.assert_called_once()

    def test_fetch_match_custom_base_url(self, example_html: str, mock_httpx_client: MagicMock) -> None:
        """Test fetch_match with custom base_url."""
        with (
            patch("cze_wp_scraper.scraper.client.httpx.Client", return_value=mock_httpx_client),
            HTTPMatchClient(base_url="https://custom.example.com") as client,
        ):
            result = client.fetch_match(123)

            assert result == example_html
            mock_httpx_client.get.assert_called_once_with("https://custom.example.com/zapas/123")

    def test_fetch_match_invalid_id_zero(self, mock_httpx_client: MagicMock) -> None:
        """Test fetch_match raises ValueError for match_id = 0."""
        with (
            patch("cze_wp_scraper.scraper.client.httpx.Client", return_value=mock_httpx_client),
            HTTPMatchClient() as client,
            pytest.raises(ValueError, match="match_id must be positive, got 0"),
        ):
            client.fetch_match(0)

    def test_fetch_match_invalid_id_negative(self, mock_httpx_client: MagicMock) -> None:
        """Test fetch_match raises ValueError for negative match_id."""
        with (
            patch("cze_wp_scraper.scraper.client.httpx.Client", return_value=mock_httpx_client),
            HTTPMatchClient() as client,
            pytest.raises(ValueError, match="match_id must be positive, got -1"),
        ):
            client.fetch_match(-1)

    def test_fetch_match_without_context_manager(self) -> None:
        """Test fetch_match raises RuntimeError when not used as context manager."""
        client = HTTPMatchClient()
        with pytest.raises(RuntimeError, match="MatchClient must be used as context manager"):
            client.fetch_match(2425)

    def test_fetch_match_http_error_404(self, mock_httpx_client: MagicMock) -> None:
        """Test fetch_match raises HTTPError for 404 Not Found."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found",
            request=MagicMock(),
            response=mock_response,
        )
        mock_httpx_client.get.return_value = mock_response

        with (
            patch("cze_wp_scraper.scraper.client.httpx.Client", return_value=mock_httpx_client),
            HTTPMatchClient() as client,
            pytest.raises(httpx.HTTPStatusError),
        ):
            client.fetch_match(9999)

    def test_fetch_match_http_error_500(self, mock_httpx_client: MagicMock) -> None:
        """Test fetch_match raises HTTPError for 500 Internal Server Error."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500 Internal Server Error",
            request=MagicMock(),
            response=mock_response,
        )
        mock_httpx_client.get.return_value = mock_response

        with (
            patch("cze_wp_scraper.scraper.client.httpx.Client", return_value=mock_httpx_client),
            HTTPMatchClient() as client,
            pytest.raises(httpx.HTTPStatusError),
        ):
            client.fetch_match(2425)

    def test_fetch_match_timeout(self, mock_httpx_client: MagicMock) -> None:
        """Test fetch_match raises TimeoutException on timeout."""
        mock_httpx_client.get.side_effect = httpx.TimeoutException("Request timed out")

        with (
            patch("cze_wp_scraper.scraper.client.httpx.Client", return_value=mock_httpx_client),
            HTTPMatchClient() as client,
            pytest.raises(httpx.TimeoutException, match="Request timed out"),
        ):
            client.fetch_match(2425)

    def test_fetch_match_network_error(self, mock_httpx_client: MagicMock) -> None:
        """Test fetch_match raises RequestError on network error."""
        mock_httpx_client.get.side_effect = httpx.RequestError("Network error", request=MagicMock())

        with (
            patch("cze_wp_scraper.scraper.client.httpx.Client", return_value=mock_httpx_client),
            HTTPMatchClient() as client,
            pytest.raises(httpx.RequestError),
        ):
            client.fetch_match(2425)

    def test_fetch_match_custom_timeout(self, mock_httpx_client: MagicMock) -> None:
        """Test that custom timeout is passed to httpx.Client."""
        with patch("cze_wp_scraper.scraper.client.httpx.Client") as mock_client_class:
            mock_client_class.return_value = mock_httpx_client

            with HTTPMatchClient(timeout=60.0) as client:
                client.fetch_match(2425)

                # Verify timeout was passed to httpx.Client
                assert mock_client_class.call_args[1]["timeout"] == 60.0

    def test_fetch_match_custom_user_agent(self, mock_httpx_client: MagicMock) -> None:
        """Test that custom user agent is passed to httpx.Client."""
        custom_agent = "MyCustomBot/1.0"
        with patch("cze_wp_scraper.scraper.client.httpx.Client") as mock_client_class:
            mock_client_class.return_value = mock_httpx_client

            with HTTPMatchClient(user_agent=custom_agent) as client:
                client.fetch_match(2425)

                # Verify user agent was passed to httpx.Client
                headers = mock_client_class.call_args[1]["headers"]
                assert headers["User-Agent"] == custom_agent

    def test_fetch_match_multiple_calls(self, example_html: str, mock_httpx_client: MagicMock) -> None:
        """Test multiple fetch_match calls reuse the same client."""
        with (
            patch("cze_wp_scraper.scraper.client.httpx.Client", return_value=mock_httpx_client),
            HTTPMatchClient() as client,
        ):
            result1 = client.fetch_match(2425)
            result2 = client.fetch_match(2426)

            assert result1 == example_html
            assert result2 == example_html
            assert mock_httpx_client.get.call_count == 2
            assert mock_httpx_client.get.call_args_list[0][0][0] == "https://www.csvp.cz/zapas/2425"
            assert mock_httpx_client.get.call_args_list[1][0][0] == "https://www.csvp.cz/zapas/2426"
