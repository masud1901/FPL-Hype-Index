"""
FBRef scraper implementation for comprehensive football statistics.
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from urllib.parse import urljoin, quote

from scrapers.base.base_scraper import BaseScraper
from scrapers.base.exceptions import ScraperDataValidationError
from .models import (
    FBRefPlayer,
    FBRefTeam,
    FBRefMatch,
    FBRefPlayerStats,
    FBRefScrapedData,
)


class FBRefScraper(BaseScraper):
    """Scraper for FBRef comprehensive football statistics."""

    def __init__(self, season: str = "2024", league: str = "Premier League"):
        """Initialize the FBRef scraper.

        Args:
            season: Season year (e.g., "2024" for 2023/24 season)
            league: League name (default: "Premier League")
        """
        super().__init__("fbref")
        self.season = season
        self.league = league
        self.base_url = "https://fbref.com"

        # League mappings
        self.league_mappings = {
            "Premier League": "en/comps/9",
            "La Liga": "en/comps/12",
            "Bundesliga": "en/comps/20",
            "Serie A": "en/comps/11",
            "Ligue 1": "en/comps/13",
        }

        # Season mappings (FBRef uses different format)
        self.season_mappings = {
            "2024": "2023-2024",  # 2023/24 season
            "2023": "2022-2023",  # 2022/23 season
            "2022": "2021-2022",  # 2021/22 season
        }

    async def scrape(self) -> Dict[str, Any]:
        """Scrape data from FBRef.

        Returns:
            Dictionary containing scraped FBRef data
        """
        try:
            self.logger.logger.info(
                f"Starting FBRef scraping",
                scraper=self.name,
                season=self.season,
                league=self.league,
            )

            # Get league and season identifiers
            league_id = self.league_mappings.get(self.league, "en/comps/9")
            season_id = self.season_mappings.get(
                self.season, f"{int(self.season)-1}-{self.season}"
            )

            # Scrape players data
            players = await self._scrape_players(league_id, season_id)

            # Scrape teams data
            teams = await self._scrape_teams(league_id, season_id)

            # Scrape matches data
            matches = await self._scrape_matches(league_id, season_id)

            # Create player stats from players data
            player_stats = self._create_player_stats(players)

            # Create standardized response
            scraped_data = FBRefScrapedData(
                players=players,
                teams=teams,
                matches=matches,
                player_stats=player_stats,
                scraped_at=datetime.utcnow(),
                source="fbref",
                season=self.season,
                league=self.league,
            )

            self.logger.logger.info(
                f"FBRef scraping completed",
                scraper=self.name,
                players_count=len(players),
                teams_count=len(teams),
                matches_count=len(matches),
                player_stats_count=len(player_stats),
            )

            return scraped_data.dict()

        except Exception as e:
            self.logger.logger.error(
                f"Failed to scrape FBRef data", scraper=self.name, error=str(e)
            )
            raise

    async def _scrape_players(
        self, league_id: str, season_id: str
    ) -> List[FBRefPlayer]:
        """Scrape players data from FBRef.

        Args:
            league_id: League identifier
            season_id: Season identifier

        Returns:
            List of FBRefPlayer objects
        """
        try:
            # FBRef stats page URL
            url = f"{self.base_url}/{league_id}/stats/{season_id}/"

            # Get the page content
            page_content = await self._make_request(url)

            # Extract the players data from HTML tables
            players_data = self._extract_players_data(page_content)

            # Parse players data
            players = []
            for player_data in players_data:
                try:
                    # Clean and transform the data
                    cleaned_data = self._clean_player_data(player_data)
                    player = FBRefPlayer(**cleaned_data)
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

    async def _scrape_teams(self, league_id: str, season_id: str) -> List[FBRefTeam]:
        """Scrape teams data from FBRef.

        Args:
            league_id: League identifier
            season_id: Season identifier

        Returns:
            List of FBRefTeam objects
        """
        try:
            # For now, we'll create basic team data
            # In a full implementation, we'd scrape team-specific pages
            teams = []

            # Common Premier League teams (this would be scraped in full implementation)
            premier_league_teams = [
                {"id": "arsenal", "name": "Arsenal", "short_name": "ARS"},
                {"id": "aston-villa", "name": "Aston Villa", "short_name": "AVL"},
                {"id": "bournemouth", "name": "Bournemouth", "short_name": "BOU"},
                {"id": "brentford", "name": "Brentford", "short_name": "BRE"},
                {
                    "id": "brighton",
                    "name": "Brighton & Hove Albion",
                    "short_name": "BHA",
                },
                {"id": "burnley", "name": "Burnley", "short_name": "BUR"},
                {"id": "chelsea", "name": "Chelsea", "short_name": "CHE"},
                {"id": "crystal-palace", "name": "Crystal Palace", "short_name": "CRY"},
                {"id": "everton", "name": "Everton", "short_name": "EVE"},
                {"id": "fulham", "name": "Fulham", "short_name": "FUL"},
                {"id": "liverpool", "name": "Liverpool", "short_name": "LIV"},
                {"id": "luton", "name": "Luton Town", "short_name": "LUT"},
                {
                    "id": "manchester-city",
                    "name": "Manchester City",
                    "short_name": "MCI",
                },
                {
                    "id": "manchester-united",
                    "name": "Manchester United",
                    "short_name": "MUN",
                },
                {"id": "newcastle", "name": "Newcastle United", "short_name": "NEW"},
                {
                    "id": "nottingham-forest",
                    "name": "Nottingham Forest",
                    "short_name": "NFO",
                },
                {
                    "id": "sheffield-united",
                    "name": "Sheffield United",
                    "short_name": "SHU",
                },
                {"id": "tottenham", "name": "Tottenham Hotspur", "short_name": "TOT"},
                {"id": "west-ham", "name": "West Ham United", "short_name": "WHU"},
                {
                    "id": "wolves",
                    "name": "Wolverhampton Wanderers",
                    "short_name": "WOL",
                },
            ]

            for team_data in premier_league_teams:
                team = FBRefTeam(
                    id=team_data["id"],
                    name=team_data["name"],
                    short_name=team_data["short_name"],
                    season=self.season,
                    league=self.league,
                )
                teams.append(team)

            return teams

        except Exception as e:
            self.logger.logger.error(
                f"Failed to scrape teams data", scraper=self.name, error=str(e)
            )
            raise

    async def _scrape_matches(self, league_id: str, season_id: str) -> List[FBRefMatch]:
        """Scrape matches data from FBRef.

        Args:
            league_id: League identifier
            season_id: Season identifier

        Returns:
            List of FBRefMatch objects
        """
        try:
            # For now, return empty list as match data requires more complex scraping
            # In a full implementation, we'd scrape match-specific pages
            matches = []

            # TODO: Implement match scraping logic
            # This would involve scraping individual match pages for detailed stats

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
            # Look for the stats table in the HTML
            # FBRef typically has stats in table format
            pattern = r'<table[^>]*id="stats_standard_squads"[^>]*>(.*?)</table>'
            match = re.search(pattern, page_content, re.DOTALL)

            if match:
                table_content = match.group(1)
                # Parse table rows to extract player data
                players_data = self._parse_stats_table(table_content)
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

    def _parse_stats_table(self, table_content: str) -> List[Dict[str, Any]]:
        """Parse stats table to extract player data.

        Args:
            table_content: HTML table content

        Returns:
            List of player data dictionaries
        """
        try:
            players_data = []

            # Extract table rows
            row_pattern = r"<tr[^>]*>(.*?)</tr>"
            rows = re.findall(row_pattern, table_content, re.DOTALL)

            for row in rows:
                # Skip header rows
                if "thead" in row or "th" in row:
                    continue

                # Extract cell data
                cell_pattern = r"<td[^>]*>(.*?)</td>"
                cells = re.findall(cell_pattern, row, re.DOTALL)

                if len(cells) >= 10:  # Minimum expected columns
                    player_data = self._parse_player_row(cells)
                    if player_data:
                        players_data.append(player_data)

            return players_data

        except Exception as e:
            self.logger.logger.error(
                f"Failed to parse stats table", scraper=self.name, error=str(e)
            )
            return []

    def _parse_player_row(self, cells: List[str]) -> Optional[Dict[str, Any]]:
        """Parse a single player row from table cells.

        Args:
            cells: List of table cell contents

        Returns:
            Player data dictionary or None if invalid
        """
        try:
            if len(cells) < 10:
                return None

            # Clean cell content (remove HTML tags)
            clean_cells = [self._clean_html(cell) for cell in cells]

            # Map cells to player data (this is a simplified mapping)
            player_data = {
                "id": f"fbref_{hash(clean_cells[0])}",  # Generate ID from name
                "name": clean_cells[0] if clean_cells[0] else "Unknown",
                "team": clean_cells[1] if len(clean_cells) > 1 else "Unknown",
                "position": clean_cells[2] if len(clean_cells) > 2 else None,
                "games": self._parse_int(clean_cells[3]) if len(clean_cells) > 3 else 0,
                "minutes": (
                    self._parse_int(clean_cells[4]) if len(clean_cells) > 4 else 0
                ),
                "goals": self._parse_int(clean_cells[5]) if len(clean_cells) > 5 else 0,
                "assists": (
                    self._parse_int(clean_cells[6]) if len(clean_cells) > 6 else 0
                ),
                "xg": (
                    self._parse_float(clean_cells[7]) if len(clean_cells) > 7 else 0.0
                ),
                "xa": (
                    self._parse_float(clean_cells[8]) if len(clean_cells) > 8 else 0.0
                ),
                "season": self.season,
                "league": self.league,
            }

            return player_data

        except Exception as e:
            self.logger.logger.warning(
                f"Failed to parse player row", scraper=self.name, error=str(e)
            )
            return None

    def _clean_html(self, html_content: str) -> str:
        """Clean HTML content to extract text.

        Args:
            html_content: HTML content

        Returns:
            Cleaned text content
        """
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", html_content)
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _parse_int(self, value: str) -> int:
        """Parse string to integer.

        Args:
            value: String value

        Returns:
            Integer value or 0 if parsing fails
        """
        try:
            # Remove any non-numeric characters except minus
            clean_value = re.sub(r"[^\d\-]", "", value)
            return int(clean_value) if clean_value else 0
        except (ValueError, TypeError):
            return 0

    def _parse_float(self, value: str) -> float:
        """Parse string to float.

        Args:
            value: String value

        Returns:
            Float value or 0.0 if parsing fails
        """
        try:
            # Remove any non-numeric characters except minus and decimal
            clean_value = re.sub(r"[^\d\-\.]", "", value)
            return float(clean_value) if clean_value else 0.0
        except (ValueError, TypeError):
            return 0.0

    def _clean_player_data(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and transform player data.

        Args:
            player_data: Raw player data from FBRef

        Returns:
            Cleaned player data
        """
        try:
            # Ensure all required fields are present
            cleaned_data = {
                "id": player_data.get("id", ""),
                "name": player_data.get("name", ""),
                "team": player_data.get("team", ""),
                "position": player_data.get("position"),
                "nationality": player_data.get("nationality"),
                "age": player_data.get("age"),
                "height": player_data.get("height"),
                "weight": player_data.get("weight"),
                "season": self.season,
                "league": self.league,
                "games": int(player_data.get("games", 0)),
                "minutes": int(player_data.get("minutes", 0)),
                "goals": int(player_data.get("goals", 0)),
                "assists": int(player_data.get("assists", 0)),
                "xg": float(player_data.get("xg", 0.0)),
                "xa": float(player_data.get("xa", 0.0)),
                "npxg": float(player_data.get("npxg", 0.0)),
                "npxg_xa": float(player_data.get("npxg_xa", 0.0)),
            }

            return cleaned_data

        except Exception as e:
            self.logger.logger.error(
                f"Failed to clean player data", scraper=self.name, error=str(e)
            )
            raise

    def _create_player_stats(
        self, players: List[FBRefPlayer]
    ) -> List[FBRefPlayerStats]:
        """Create player stats from players data.

        Args:
            players: List of FBRefPlayer objects

        Returns:
            List of FBRefPlayerStats objects
        """
        try:
            player_stats = []

            for player in players:
                # Calculate per-90 stats
                minutes = player.minutes if player.minutes > 0 else 1
                goals_per_90 = (player.goals * 90) / minutes
                assists_per_90 = (player.assists * 90) / minutes
                goals_assists_per_90 = goals_per_90 + assists_per_90
                xg_per_90 = (player.xg * 90) / minutes
                xa_per_90 = (player.xa * 90) / minutes
                npxg_per_90 = (player.npxg * 90) / minutes
                npxg_xa_per_90 = (player.npxg_xa * 90) / minutes

                stats = FBRefPlayerStats(
                    player_id=player.id,
                    player_name=player.name,
                    team=player.team,
                    season=self.season,
                    league=self.league,
                    games=player.games,
                    minutes=player.minutes,
                    goals=player.goals,
                    assists=player.assists,
                    xg=player.xg,
                    xa=player.xa,
                    npxg=player.npxg,
                    npxg_xa=player.npxg_xa,
                    goals_per_90=goals_per_90,
                    assists_per_90=assists_per_90,
                    goals_assists_per_90=goals_assists_per_90,
                    xg_per_90=xg_per_90,
                    xa_per_90=xa_per_90,
                    npxg_per_90=npxg_per_90,
                    npxg_xa_per_90=npxg_xa_per_90,
                )
                player_stats.append(stats)

            return player_stats

        except Exception as e:
            self.logger.logger.error(
                f"Failed to create player stats", scraper=self.name, error=str(e)
            )
            raise

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate scraped FBRef data.

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
                    f"Missing required keys in FBRef data",
                    scraper=self.name,
                    required_keys=required_keys,
                    actual_keys=list(data.keys()),
                )
                return False

            # Check if source is correct
            if data.get("source") != "fbref":
                self.logger.logger.warning(
                    f"Incorrect source in FBRef data",
                    scraper=self.name,
                    expected_source="fbref",
                    actual_source=data.get("source"),
                )
                return False

            # Check if we have players data
            players = data.get("players", [])
            if not players:
                self.logger.logger.warning(
                    f"No players data found in FBRef response", scraper=self.name
                )
                return False

            # Check if we have teams data
            teams = data.get("teams", [])
            if not teams:
                self.logger.logger.warning(
                    f"No teams data found in FBRef response", scraper=self.name
                )
                return False

            # Validate player data structure
            for player in players[:5]:  # Check first 5 players
                if not isinstance(player, dict):
                    continue

                required_player_fields = ["id", "name", "team", "season", "league"]
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
                f"FBRef data validation successful",
                scraper=self.name,
                players_count=len(players),
                teams_count=len(teams),
                matches_count=len(data.get("matches", [])),
                player_stats_count=len(data.get("player_stats", [])),
            )

            return True

        except Exception as e:
            self.logger.logger.error(
                f"Error during FBRef data validation", scraper=self.name, error=str(e)
            )
            return False
