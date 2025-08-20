"""
FPL API scraper implementation.
"""

import json
from typing import Dict, Any, List
from datetime import datetime
from scrapers.base.base_scraper import BaseScraper
from scrapers.base.exceptions import ScraperDataValidationError
from .models import (
    FPLPlayer,
    FPLTeam,
    FPLGameweek,
    FPLFixture,
    FPLBootstrapData,
    FPLScrapedData,
)


class FPLScraper(BaseScraper):
    """Scraper for the official FPL API."""

    def __init__(self):
        """Initialize the FPL scraper."""
        super().__init__("fpl_api")
        self.base_url = self.config.fpl_api_url.rstrip("/")

    async def scrape(self) -> Dict[str, Any]:
        """Scrape data from the FPL API.

        Returns:
            Dictionary containing scraped FPL data
        """
        try:
            # Fetch bootstrap data (contains players, teams, gameweeks)
            bootstrap_url = f"{self.base_url}/bootstrap-static/"
            bootstrap_data = await self._make_request(bootstrap_url)

            # Fetch fixtures data
            fixtures_url = f"{self.base_url}/fixtures/"
            fixtures_data = await self._make_request(fixtures_url)

            # Parse the bootstrap data
            parsed_data = self._parse_bootstrap_data(bootstrap_data)

            # Parse fixtures data
            fixtures = self._parse_fixtures_data(fixtures_data)

            # Create standardized response
            scraped_data = FPLScrapedData(
                players=parsed_data["players"],
                teams=parsed_data["teams"],
                gameweeks=parsed_data["gameweeks"],
                fixtures=fixtures,
                scraped_at=datetime.utcnow(),
                source="fpl_api",
            )

            return scraped_data.dict()

        except Exception as e:
            self.logger.logger.error(
                "Failed to scrape FPL API data", scraper=self.name, error=str(e)
            )
            raise

    def _parse_bootstrap_data(self, data: Dict[str, Any]) -> Dict[str, List]:
        """Parse bootstrap data from FPL API.

        Args:
            data: Raw bootstrap data from FPL API

        Returns:
            Parsed data with players, teams, and gameweeks
        """
        try:
            # Parse players
            players = []
            for player_data in data.get("elements", []):
                try:
                    player = FPLPlayer(**player_data)
                    players.append(player)
                except Exception as e:
                    self.logger.logger.warning(
                        "Failed to parse player data",
                        scraper=self.name,
                        player_id=player_data.get("id"),
                        error=str(e),
                    )

            # Parse teams
            teams = []
            for team_data in data.get("teams", []):
                try:
                    team = FPLTeam(**team_data)
                    teams.append(team)
                except Exception as e:
                    self.logger.logger.warning(
                        "Failed to parse team data",
                        scraper=self.name,
                        team_id=team_data.get("id"),
                        error=str(e),
                    )

            # Parse gameweeks
            gameweeks = []
            for event_data in data.get("events", []):
                try:
                    # Convert deadline_time string to datetime
                    if "deadline_time" in event_data:
                        event_data["deadline_time"] = datetime.fromisoformat(
                            event_data["deadline_time"].replace("Z", "+00:00")
                        )
                    gameweek = FPLGameweek(**event_data)
                    gameweeks.append(gameweek)
                except Exception as e:
                    self.logger.logger.warning(
                        "Failed to parse gameweek data",
                        scraper=self.name,
                        gameweek_id=event_data.get("id"),
                        error=str(e),
                    )

            self.logger.logger.info(
                "Successfully parsed bootstrap data",
                scraper=self.name,
                players_count=len(players),
                teams_count=len(teams),
                gameweeks_count=len(gameweeks),
            )

            return {"players": players, "teams": teams, "gameweeks": gameweeks}

        except Exception as e:
            self.logger.logger.error(
                "Failed to parse bootstrap data", scraper=self.name, error=str(e)
            )
            raise

    def _parse_fixtures_data(self, data: List[Dict[str, Any]]) -> List[FPLFixture]:
        """Parse fixtures data from FPL API.

        Args:
            data: Raw fixtures data from FPL API

        Returns:
            List of parsed fixtures
        """
        try:
            fixtures = []
            for fixture_data in data:
                try:
                    # Convert kickoff_time string to datetime
                    if "kickoff_time" in fixture_data:
                        fixture_data["kickoff_time"] = datetime.fromisoformat(
                            fixture_data["kickoff_time"].replace("Z", "+00:00")
                        )
                    fixture = FPLFixture(**fixture_data)
                    fixtures.append(fixture)
                except Exception as e:
                    self.logger.logger.warning(
                        "Failed to parse fixture data",
                        scraper=self.name,
                        fixture_id=fixture_data.get("id"),
                        error=str(e),
                    )

            self.logger.logger.info(
                "Successfully parsed fixtures data",
                scraper=self.name,
                fixtures_count=len(fixtures),
            )

            return fixtures

        except Exception as e:
            self.logger.logger.error(
                "Failed to parse fixtures data", scraper=self.name, error=str(e)
            )
            raise

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate scraped FPL data.

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
                "gameweeks",
                "fixtures",
                "scraped_at",
                "source",
            ]
            if not all(key in data for key in required_keys):
                self.logger.logger.warning(
                    "Missing required keys in FPL data",
                    scraper=self.name,
                    required_keys=required_keys,
                    actual_keys=list(data.keys()),
                )
                return False

            # Check if source is correct
            if data.get("source") != "fpl_api":
                self.logger.logger.warning(
                    "Incorrect source in FPL data",
                    scraper=self.name,
                    expected_source="fpl_api",
                    actual_source=data.get("source"),
                )
                return False

            # Check if we have players data
            players = data.get("players", [])
            if not players:
                self.logger.logger.warning(
                    "No players data found in FPL response", scraper=self.name
                )
                return False

            # Check if we have teams data
            teams = data.get("teams", [])
            if not teams:
                self.logger.logger.warning(
                    "No teams data found in FPL response", scraper=self.name
                )
                return False

            # Check if we have gameweeks data
            gameweeks = data.get("gameweeks", [])
            if not gameweeks:
                self.logger.logger.warning(
                    "No gameweeks data found in FPL response", scraper=self.name
                )
                return False

            # Check if we have fixtures data
            fixtures = data.get("fixtures", [])
            if not fixtures:
                self.logger.logger.warning(
                    "No fixtures data found in FPL response", scraper=self.name
                )
                return False

            # Validate player data structure
            for player in players[:5]:  # Check first 5 players
                if not isinstance(player, dict):
                    continue

                required_player_fields = [
                    "id",
                    "first_name",
                    "second_name",
                    "team",
                    "element_type",
                ]
                if not all(field in player for field in required_player_fields):
                    self.logger.logger.warning(
                        "Player missing required fields",
                        scraper=self.name,
                        player_id=player.get("id"),
                        required_fields=required_player_fields,
                        actual_fields=list(player.keys()),
                    )
                    return False

            self.logger.logger.info(
                "FPL data validation successful",
                scraper=self.name,
                players_count=len(players),
                teams_count=len(teams),
                gameweeks_count=len(gameweeks),
            )

            return True

        except Exception as e:
            self.logger.logger.error(
                "Error during FPL data validation", scraper=self.name, error=str(e)
            )
            return False

    async def get_player_details(self, player_id: int) -> Dict[str, Any]:
        """Get detailed information for a specific player.

        Args:
            player_id: FPL player ID

        Returns:
            Player details
        """
        try:
            url = f"{self.base_url}/element-summary/{player_id}/"
            data = await self._make_request(url)

            self.logger.logger.info(
                "Retrieved player details", scraper=self.name, player_id=player_id
            )

            return data

        except Exception as e:
            self.logger.logger.error(
                "Failed to get player details",
                scraper=self.name,
                player_id=player_id,
                error=str(e),
            )
            raise

    async def get_gameweek_data(self, gameweek: int) -> Dict[str, Any]:
        """Get data for a specific gameweek.

        Args:
            gameweek: Gameweek number

        Returns:
            Gameweek data
        """
        try:
            url = f"{self.base_url}/event/{gameweek}/live/"
            data = await self._make_request(url)

            self.logger.logger.info(
                "Retrieved gameweek data", scraper=self.name, gameweek=gameweek
            )

            return data

        except Exception as e:
            self.logger.logger.error(
                "Failed to get gameweek data",
                scraper=self.name,
                gameweek=gameweek,
                error=str(e),
            )
            raise
