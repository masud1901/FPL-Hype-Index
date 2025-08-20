"""
Data models for Transfermarkt scraper.
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class TransfermarktPlayer:
    """Model for Transfermarkt player data."""

    id: str
    name: str
    url: str
    position: str
    age: int
    market_value: float
    contract_until: str
    last_club: str
    source: str = "transfermarkt"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "position": self.position,
            "age": self.age,
            "market_value": self.market_value,
            "contract_until": self.contract_until,
            "last_club": self.last_club,
            "source": self.source,
        }


@dataclass
class TransfermarktTeam:
    """Model for Transfermarkt team data."""

    id: str
    name: str
    url: str
    squad_size: int
    league: str
    season: str
    source: str = "transfermarkt"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "squad_size": self.squad_size,
            "league": self.league,
            "season": self.season,
            "source": self.source,
        }


@dataclass
class TransfermarktTransfer:
    """Model for Transfermarkt transfer data."""

    player_name: str
    position: str
    age: int
    transfer_type: str  # "in" or "out"
    fee: float
    date: str
    source: str = "transfermarkt"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "player_name": self.player_name,
            "position": self.position,
            "age": self.age,
            "transfer_type": self.transfer_type,
            "fee": self.fee,
            "date": self.date,
            "source": self.source,
        }


@dataclass
class TransfermarktData:
    """Complete Transfermarkt dataset."""

    players: List[TransfermarktPlayer]
    teams: List[TransfermarktTeam]
    transfers: List[TransfermarktTransfer]
    scraped_at: datetime
    source: str = "transfermarkt"
    season: str = "2024/25"
    league: str = "Premier League"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "players": [player.to_dict() for player in self.players],
            "teams": [team.to_dict() for team in self.teams],
            "transfers": [transfer.to_dict() for transfer in self.transfers],
            "scraped_at": self.scraped_at.isoformat(),
            "source": self.source,
            "season": self.season,
            "league": self.league,
        }
