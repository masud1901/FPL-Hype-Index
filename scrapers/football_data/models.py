"""
Data models for Football-Data scraper.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class FootballDataTeam:
    """Model for Football-Data team information."""

    id: int
    name: str
    short_name: str
    tla: str
    crest: str
    website: Optional[str] = None
    founded: Optional[int] = None
    club_colors: Optional[str] = None
    venue: Optional[Dict[str, Any]] = None
    source: str = "football_data"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "short_name": self.short_name,
            "tla": self.tla,
            "crest": self.crest,
            "website": self.website,
            "founded": self.founded,
            "club_colors": self.club_colors,
            "venue": self.venue,
            "source": self.source,
        }


@dataclass
class FootballDataMatch:
    """Model for Football-Data match information."""

    id: int
    home_team: Dict[str, Any]
    away_team: Dict[str, Any]
    score: Dict[str, Any]
    status: str
    stage: str
    group: Optional[str] = None
    last_updated: str = ""
    utc_date: str = ""
    matchday: int = 0
    season: Dict[str, Any] = None
    source: str = "football_data"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "score": self.score,
            "status": self.status,
            "stage": self.stage,
            "group": self.group,
            "last_updated": self.last_updated,
            "utc_date": self.utc_date,
            "matchday": self.matchday,
            "season": self.season,
            "source": self.source,
        }


@dataclass
class FootballDataFixture:
    """Model for Football-Data fixture information."""

    id: int
    home_team: Dict[str, Any]
    away_team: Dict[str, Any]
    status: str
    stage: str
    group: Optional[str] = None
    last_updated: str = ""
    utc_date: str = ""
    matchday: int = 0
    season: Dict[str, Any] = None
    source: str = "football_data"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "status": self.status,
            "stage": self.stage,
            "group": self.group,
            "last_updated": self.last_updated,
            "utc_date": self.utc_date,
            "matchday": self.matchday,
            "season": self.season,
            "source": self.source,
        }


@dataclass
class FootballDataLeague:
    """Model for Football-Data league information."""

    id: int
    name: str
    code: str
    emblem: str
    current_season: Dict[str, Any]
    seasons: List[Dict[str, Any]]

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "emblem": self.emblem,
            "current_season": self.current_season,
            "seasons": self.seasons,
        }


@dataclass
class FootballDataData:
    """Complete Football-Data dataset."""

    teams: List[FootballDataTeam]
    matches: List[FootballDataMatch]
    fixtures: List[FootballDataFixture]
    league: FootballDataLeague
    scraped_at: datetime
    source: str = "football_data"
    season: str = "2024/25"
    league_name: str = "Premier League"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "teams": [team.to_dict() for team in self.teams],
            "matches": [match.to_dict() for match in self.matches],
            "fixtures": [fixture.to_dict() for fixture in self.fixtures],
            "league": self.league.to_dict() if self.league else {},
            "scraped_at": self.scraped_at.isoformat(),
            "source": self.source,
            "season": self.season,
            "league_name": self.league_name,
        }
