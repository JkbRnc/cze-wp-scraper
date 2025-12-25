from __future__ import annotations


class MatchParsingError(Exception):
    """Exception raised when parsing fails."""

    def __init__(self, message: str) -> None:
        """Initialize the MatchParsingError.

        Args:
            message: The message to display.
        """
        self.message = message
        super().__init__(self.message)
