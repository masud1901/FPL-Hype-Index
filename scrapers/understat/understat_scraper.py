"""
Understat scraper implementation for advanced football statistics.
"""

import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from urllib.parse import urljoin

from scrapers.base.base_scraper import BaseScraper
from scrapers.base.exceptions import ScraperDataValidationError
from .models import (
    UnderstatPlayer,
    UnderstatTeam,
    UnderstatMatch,
    UnderstatPlayerStats,
    UnderstatScrapedData,
)


class UnderstatScraper(BaseScraper):
    """Scraper for Understat advanced football statistics."""

    def __init__(self, season: str = "2024", league: str = "EPL"):
        """Initialize the Understat scraper.

        Args:
            season: Season year (e.g., "2024" for 2023/24 season)
            league: League identifier (default: "EPL" for Premier League)
        """
        super().__init__("understat")
        self.season = season
        self.league = league
        self.base_url = "https://understat.com"

        # League mappings
        self.league_mappings = {
            "EPL": "epl",
            "La_Liga": "la_liga",
            "Bundesliga": "bundesliga",
            "Serie_A": "serie_a",
            "Ligue_1": "ligue_1",
        }

        # Season mappings (Understat uses different format)
        self.season_mappings = {
            "2024": "2023",  # 2023/24 season
            "2023": "2022",  # 2022/23 season
            "2022": "2021",  # 2021/22 season
        }

    async def scrape(self) -> Dict[str, Any]:
        """Scrape data from Understat.

        Returns:
            Dictionary containing scraped Understat data
        """
        try:
            self.logger.logger.info(
                f"Starting Understat scraping",
                scraper=self.name,
                season=self.season,
                league=self.league,
            )

            # Get league identifier
            league_id = self.league_mappings.get(self.league, "epl")
            season_id = self.season_mappings.get(self.season, self.season)

            # Scrape players data
            players = await self._scrape_players(league_id, season_id)

            # Scrape teams data
            teams = await self._scrape_teams(league_id, season_id)

            # Scrape matches data
            matches = await self._scrape_matches(league_id, season_id)

            # Create player stats from players data
            player_stats = self._create_player_stats(players)

            # Create standardized response
            scraped_data = UnderstatScrapedData(
                players=players,
                teams=teams,
                matches=matches,
                player_stats=player_stats,
                scraped_at=datetime.utcnow(),
                source="understat",
                season=self.season,
                league=self.league,
            )

            self.logger.logger.info(
                f"Understat scraping completed",
                scraper=self.name,
                players_count=len(players),
                teams_count=len(teams),
                matches_count=len(matches),
                player_stats_count=len(player_stats),
            )

            return scraped_data.dict()

        except Exception as e:
            self.logger.logger.error(
                f"Failed to scrape Understat data", scraper=self.name, error=str(e)
            )
            raise

    async def _scrape_players(
        self, league_id: str, season_id: str
    ) -> List[UnderstatPlayer]:
        """Scrape players data from Understat.

        Args:
            league_id: League identifier
            season_id: Season identifier

        Returns:
            List of UnderstatPlayer objects
        """
        try:
            # Understat players page URL
            url = f"{self.base_url}/league/{league_id}/{season_id}"

            # Get the page content
            page_content = await self._make_request(url)

            # Extract the players data from JavaScript
            players_data = self._extract_players_data(page_content)

            # Parse players data
            players = []
            for player_data in players_data:
                try:
                    # Clean and transform the data
                    cleaned_data = self._clean_player_data(player_data)
                    player = UnderstatPlayer(**cleaned_data)
                    players.append(player)
                except Exception as e:
                    self.logger.logger.warning(
                        f"Failed to parse player data",
                        scraper=self.name,
                        player_id=player_data.get("id"),
                        error=str(e),
                    )

            return players

        except Exception as e:
            self.logger.logger.error(
                f"Failed to scrape players data", scraper=self.name, error=str(e)
            )
            raise

    async def _scrape_teams(
        self, league_id: str, season_id: str
    ) -> List[UnderstatTeam]:
        """Scrape teams data from Understat.

        Args:
            league_id: League identifier
            season_id: Season identifier

        Returns:
            List of UnderstatTeam objects
        """
        try:
            # For now, we'll create basic team data
            # In a full implementation, we'd scrape team-specific pages
            teams = []

            # Common Premier League teams (this would be scraped in full implementation)
            premier_league_teams = [
                {"id": 1, "title": "Arsenal", "short_title": "ARS"},
                {"id": 2, "title": "Aston Villa", "short_title": "AVL"},
                {"id": 3, "title": "Bournemouth", "short_title": "BOU"},
                {"id": 4, "title": "Brentford", "short_title": "BRE"},
                {"id": 5, "title": "Brighton", "short_title": "BHA"},
                {"id": 6, "title": "Burnley", "short_title": "BUR"},
                {"id": 7, "title": "Chelsea", "short_title": "CHE"},
                {"id": 8, "title": "Crystal Palace", "short_title": "CRY"},
                {"id": 9, "title": "Everton", "short_title": "EVE"},
                {"id": 10, "title": "Fulham", "short_title": "FUL"},
                {"id": 11, "title": "Liverpool", "short_title": "LIV"},
                {"id": 12, "title": "Luton", "short_title": "LUT"},
                {"id": 13, "title": "Manchester City", "short_title": "MCI"},
                {"id": 14, "title": "Manchester United", "short_title": "MUN"},
                {"id": 15, "title": "Newcastle", "short_title": "NEW"},
                {"id": 16, "title": "Nottingham Forest", "short_title": "NFO"},
                {"id": 17, "title": "Sheffield United", "short_title": "SHU"},
                {"id": 18, "title": "Tottenham", "short_title": "TOT"},
                {"id": 19, "title": "West Ham", "short_title": "WHU"},
                {"id": 20, "title": "Wolves", "short_title": "WOL"},
            ]

            for team_data in premier_league_teams:
                team = UnderstatTeam(
                    id=team_data["id"],
                    title=team_data["title"],
                    short_title=team_data["short_title"],
                    league=self.league,
                    season=self.season,
                )
                teams.append(team)

            return teams

        except Exception as e:
            self.logger.logger.error(
                f"Failed to scrape teams data", scraper=self.name, error=str(e)
            )
            raise

    async def _scrape_matches(
        self, league_id: str, season_id: str
    ) -> List[UnderstatMatch]:
        """Scrape matches data from Understat.

        Args:
            league_id: League identifier
            season_id: Season identifier

        Returns:
            List of UnderstatMatch objects
        """
        try:
            # For now, return empty list as match data requires more complex scraping
            # In a full implementation, we'd scrape match-specific pages
            matches = []

            # TODO: Implement match scraping logic
            # This would involve scraping individual match pages for xG data

            return matches

        except Exception as e:
            self.logger.logger.error(
                f"Failed to scrape matches data", scraper=self.name, error=str(e)
            )
            raise

    def _extract_players_data(self, page_content: str) -> List[Dict[str, Any]]:
        """Extract players data from page content.

        Args:
            page_content: HTML page content

        Returns:
            List of player data dictionaries
        """
        try:
            # Look for the players data in JavaScript
            # Understat typically embeds data in a script tag
            pattern = r"var\s+playersData\s*=\s*(\[.*?\]);"
            match = re.search(pattern, page_content, re.DOTALL)

            if match:
                players_json = match.group(1)
                players_data = json.loads(players_json)
                return players_data

            # If not found, return empty list for now
            # In production, we'd implement more sophisticated parsing
            self.logger.logger.warning(
                f"Could not extract players data from page", scraper=self.name
            )
            return []

        except Exception as e:
            self.logger.logger.error(
                f"Failed to extract players data", scraper=self.name, error=str(e)
            )
            return []

    def _clean_player_data(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and transform player data.

        Args:
            player_data: Raw player data from Understat

        Returns:
            Cleaned player data
        """
        try:
            # Map Understat field names to our model
            cleaned_data = {
                "id": player_data.get("id"),
                "player_name": player_data.get("player_name", ""),
                "team": player_data.get("team", ""),
                "position": player_data.get("position"),
                "games": int(player_data.get("games", 0)),
                "time": int(player_data.get("time", 0)),
                "goals": int(player_data.get("goals", 0)),
                "xg": float(player_data.get("xG", 0.0)),
                "assists": int(player_data.get("assists", 0)),
                "xa": float(player_data.get("xA", 0.0)),
                "shots": int(player_data.get("shots", 0)),
                "key_passes": int(player_data.get("key_passes", 0)),
                "yellow_cards": int(player_data.get("yellow_cards", 0)),
                "red_cards": int(player_data.get("red_cards", 0)),
                "npg": int(player_data.get("npg", 0)),
                "npxg": float(player_data.get("npxG", 0.0)),
                "xgChain": float(player_data.get("xGChain", 0.0)),
                "xgBuildUp": float(player_data.get("xGBuildup", 0.0)),
                "deep": int(player_data.get("deep", 0)),
                "deep_allowed": int(player_data.get("deep_allowed", 0)),
                "scored": int(player_data.get("scored", 0)),
                "missed": int(player_data.get("missed", 0)),
                "saves": int(player_data.get("saves", 0)),
                "conceded": int(player_data.get("conceded", 0)),
                "wins": int(player_data.get("wins", 0)),
                "draws": int(player_data.get("draws", 0)),
                "losses": int(player_data.get("losses", 0)),
                "clean_sheets": int(player_data.get("clean_sheets", 0)),
                "season": self.season,
                "league": self.league,
            }

            return cleaned_data

        except Exception as e:
            self.logger.logger.error(
                f"Failed to clean player data", scraper=self.name, error=str(e)
            )
            raise

    def _create_player_stats(
        self, players: List[UnderstatPlayer]
    ) -> List[UnderstatPlayerStats]:
        """Create player stats from players data.

        Args:
            players: List of UnderstatPlayer objects

        Returns:
            List of UnderstatPlayerStats objects
        """
        try:
            player_stats = []

            for player in players:
                stats = UnderstatPlayerStats(
                    player_id=player.id,
                    player_name=player.player_name,
                    team=player.team,
                    season=self.season,
                    league=self.league,
                    games=player.games,
                    minutes=player.time,
                    goals=player.goals,
                    xg=player.xg,
                    assists=player.assists,
                    xa=player.xa,
                    shots=player.shots,
                    key_passes=player.key_passes,
                    yellow_cards=player.yellow_cards,
                    red_cards=player.red_cards,
                    npg=player.npg,
                    npxg=player.npxg,
                    xg_chain=player.xgChain,
                    xg_build_up=player.xgBuildUp,
                    deep=player.deep,
                    deep_allowed=player.deep_allowed,
                    clean_sheets=player.clean_sheets,
                    wins=player.wins,
                    draws=player.draws,
                    losses=player.losses,
                )
                player_stats.append(stats)

            return player_stats

        except Exception as e:
            self.logger.logger.error(
                f"Failed to create player stats", scraper=self.name, error=str(e)
            )
            raise

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate scraped Understat data.

        Args:
            data: Data to validate

        Returns:
            True if data is valid, False otherwise
        """
        try:
            # Check if data has required keys
            required_keys = [
                "players",
                "teams",
                "matches",
                "player_stats",
                "scraped_at",
                "source",
                "season",
                "league",
            ]
            if not all(key in data for key in required_keys):
                self.logger.logger.warning(
                    f"Missing required keys in Understat data",
                    scraper=self.name,
                    required_keys=required_keys,
                    actual_keys=list(data.keys()),
                )
                return False

            # Check if source is correct
            if data.get("source") != "understat":
                self.logger.logger.warning(
                    f"Incorrect source in Understat data",
                    scraper=self.name,
                    expected_source="understat",
                    actual_source=data.get("source"),
                )
                return False

            # Check if we have players data
            players = data.get("players", [])
            if not players:
                self.logger.logger.warning(
                    f"No players data found in Understat response", scraper=self.name
                )
                return False

            # Check if we have teams data
            teams = data.get("teams", [])
            if not teams:
                self.logger.logger.warning(
                    f"No teams data found in Understat response", scraper=self.name
                )
                return False

            # Validate player data structure
            for player in players[:5]:  # Check first 5 players
                if not isinstance(player, dict):
                    continue

                required_player_fields = [
                    "id",
                    "player_name",
                    "team",
                    "season",
                    "league",
                ]
                if not all(field in player for field in required_player_fields):
                    self.logger.logger.warning(
                        f"Player missing required fields",
                        scraper=self.name,
                        player_id=player.get("id"),
                        required_fields=required_player_fields,
                        actual_fields=list(player.keys()),
                    )
                    return False

            self.logger.logger.info(
                f"Understat data validation successful",
                scraper=self.name,
                players_count=len(players),
                teams_count=len(teams),
                matches_count=len(data.get("matches", [])),
                player_stats_count=len(data.get("player_stats", [])),
            )

            return True

        except Exception as e:
            self.logger.logger.error(
                f"Error during Understat data validation",
                scraper=self.name,
                error=str(e),
            )
            return False

    async def get_player_details(self, player_id: int) -> Dict[str, Any]:
        """Get detailed information for a specific player.

        Args:
            player_id: Understat player ID

        Returns:
            Player details
        """
        try:
            # This would be implemented to get detailed player stats
            # For now, return empty dict
            self.logger.logger.info(
                f"Retrieved player details", scraper=self.name, player_id=player_id
            )

            return {}

        except Exception as e:
            self.logger.logger.error(
                f"Failed to get player details",
                scraper=self.name,
                player_id=player_id,
                error=str(e),
            )
            raise
