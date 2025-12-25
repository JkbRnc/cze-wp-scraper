from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator

from cze_wp_scraper.utils.constants import Constants


class MatchModel(BaseModel):
    """Pydantic model for a match info data."""

    game_id: int
    home_team: str
    away_team: str
    match_date: datetime
    league: str
    home_score: int
    away_score: int
    winner: Literal["H", "A", "D"]

    @field_validator("match_date", mode="before")
    def validate_match_date(cls, v: str | datetime) -> datetime:
        """Validate match date."""
        if isinstance(v, str):
            return datetime.strptime(v, Constants.OUTPUT_DATE_FORMAT)
        return v
