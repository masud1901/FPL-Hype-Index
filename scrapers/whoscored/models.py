"""
Data models for WhoScored scraper.
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class WhoScoredPlayer:
    """Model for WhoScored player data."""

    id: str
    name: str
    url: str
    position: str
    age: int
    rating: float
    appearances: int
    source: str = "whoscored"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "position": self.position,
            "age": self.age,
            "rating": self.rating,
            "appearances": self.appearances,
            "source": self.source,
        }


@dataclass
class WhoScoredTeam:
    """Model for WhoScored team data."""

    id: str
    name: str
    url: str
    league: str
    season: str
    source: str = "whoscored"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "league": self.league,
            "season": self.season,
            "source": self.source,
        }


@dataclass
class WhoScoredMatch:
    """Model for WhoScored match data."""

    date: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    competition: str
    result: str
    source: str = "whoscored"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "date": self.date,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "home_score": self.home_score,
            "away_score": self.away_score,
            "competition": self.competition,
            "result": self.result,
            "source": self.source,
        }


@dataclass
class WhoScoredData:
    """Complete WhoScored dataset."""

    players: List[WhoScoredPlayer]
    teams: List[WhoScoredTeam]
    matches: List[WhoScoredMatch]
    scraped_at: datetime
    source: str = "whoscored"
    season: str = "2024/25"
    league: str = "Premier League"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "players": [player.to_dict() for player in self.players],
            "teams": [team.to_dict() for team in self.teams],
            "matches": [match.to_dict() for match in self.matches],
            "scraped_at": self.scraped_at.isoformat(),
            "source": self.source,
            "season": self.season,
            "league": self.league,
        }
