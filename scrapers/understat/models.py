"""
Data models for Understat scraper.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class UnderstatPlayer(BaseModel):
    """Understat player data model."""

    id: int
    player_name: str
    team: str
    position: Optional[str] = None
    games: int = 0
    time: int = 0  # Minutes played
    goals: int = 0
    xg: float = 0.0  # Expected goals
    assists: int = 0
    xa: float = 0.0  # Expected assists
    shots: int = 0
    key_passes: int = 0
    yellow_cards: int = 0
    red_cards: int = 0
    npg: int = 0  # Non-penalty goals
    npxg: float = 0.0  # Non-penalty expected goals
    xgChain: float = 0.0  # Expected goals chain
    xgBuildUp: float = 0.0  # Expected goals build-up
    deep: int = 0  # Deep completions
    deep_allowed: int = 0
    scored: int = 0
    missed: int = 0
    saves: int = 0
    conceded: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    clean_sheets: int = 0
    season: str
    league: str = "EPL"

    class Config:
        extra = "allow"  # Allow extra fields from API


class UnderstatTeam(BaseModel):
    """Understat team data model."""

    id: int
    title: str
    short_title: str
    league: str = "EPL"
    season: str

    class Config:
        extra = "allow"


class UnderstatMatch(BaseModel):
    """Understat match data model."""

    id: int
    home_team: str
    away_team: str
    home_goals: int
    away_goals: int
    home_xg: float
    away_xg: float
    date: datetime
    season: str
    league: str = "EPL"

    class Config:
        extra = "allow"


class UnderstatPlayerStats(BaseModel):
    """Understat player statistics for a specific season."""

    player_id: int
    player_name: str
    team: str
    season: str
    league: str = "EPL"
    games: int = 0
    minutes: int = 0
    goals: int = 0
    xg: float = 0.0
    assists: int = 0
    xa: float = 0.0
    shots: int = 0
    key_passes: int = 0
    yellow_cards: int = 0
    red_cards: int = 0
    npg: int = 0
    npxg: float = 0.0
    xg_chain: float = 0.0
    xg_build_up: float = 0.0
    deep: int = 0
    deep_allowed: int = 0
    clean_sheets: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0

    class Config:
        extra = "allow"


class UnderstatScrapedData(BaseModel):
    """Complete Understat scraped data model."""

    players: List[UnderstatPlayer]
    teams: List[UnderstatTeam]
    matches: List[UnderstatMatch]
    player_stats: List[UnderstatPlayerStats]
    scraped_at: datetime
    source: str = "understat"
    season: str
    league: str = "EPL"

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class UnderstatLeagueData(BaseModel):
    """Understat league data model."""

    league_id: int
    league_name: str
    season: str
    teams: List[UnderstatTeam]
    players: List[UnderstatPlayer]
    matches: List[UnderstatMatch]

    class Config:
        extra = "allow"
