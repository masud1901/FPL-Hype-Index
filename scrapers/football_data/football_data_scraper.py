"""
Football-Data scraper for FPL Data Collection System.

This scraper collects:
- Historical match data
- Fixture information
- League standings
- Team statistics
- Player historical performance
"""

import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import json
import re

from scrapers.base.base_scraper import BaseScraper
from scrapers.base.exceptions import ScrapingError, ValidationError
from .models import FootballDataMatch, FootballDataTeam, FootballDataFixture
from utils.logger import get_logger


class FootballDataScraper(BaseScraper):
    """Football-Data scraper for historical data and fixtures."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the Football-Data scraper."""
        super().__init__(config)
        self.logger = get_logger(__name__)
        self.base_url = "https://api.football-data.org/v4"
        self.api_key = config.get("football_data_api_key", "")
        self.session = None
        self.headers = {
            "X-Auth-Token": self.api_key,
            "User-Agent": "FPL-Data-Collection/1.0",
        }

    async def scrape(self) -> Dict[str, Any]:
        """Main scraping method for Football-Data."""
        try:
            self.logger.info("Starting Football-Data collection")

            if not self.api_key:
                self.logger.warning(
                    "No API key provided for Football-Data, using limited functionality"
                )
                return await self._scrape_without_api()

            # Initialize session
            self.session = aiohttp.ClientSession(headers=self.headers)

            # Get Premier League data
            league_data = await self._get_premier_league_data()
            self.logger.info("Retrieved Premier League data")

            # Get teams
            teams = await self._get_teams()
            self.logger.info(f"Found {len(teams)} teams")

            # Get matches
            matches = await self._get_matches()
            self.logger.info(f"Found {len(matches)} matches")

            # Get fixtures
            fixtures = await self._get_fixtures()
            self.logger.info(f"Found {len(fixtures)} fixtures")

            # Compile final data
            scraped_data = {
                "teams": teams,
                "matches": matches,
                "fixtures": fixtures,
                "league": league_data,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "source": "football_data",
                "season": "2024/25",
                "league_name": "Premier League",
            }

            self.logger.info(
                "Football-Data scraping completed",
                teams_count=len(teams),
                matches_count=len(matches),
                fixtures_count=len(fixtures),
            )

            return scraped_data

        except Exception as e:
            self.logger.error(f"Football-Data scraping failed: {e}")
            raise ScrapingError(f"Failed to scrape Football-Data: {str(e)}")

        finally:
            if self.session:
                await self.session.close()

    async def _scrape_without_api(self) -> Dict[str, Any]:
        """Scrape data without API key (limited functionality)."""
        self.logger.info("Scraping Football-Data without API key")

        # Return minimal data structure
        return {
            "teams": [],
            "matches": [],
            "fixtures": [],
            "league": {},
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "source": "football_data",
            "season": "2024/25",
            "league_name": "Premier League",
            "note": "No API key provided - limited data available",
        }

    async def _get_premier_league_data(self) -> Dict[str, Any]:
        """Get Premier League competition data."""
        try:
            url = f"{self.base_url}/competitions/PL"

            async with self.session.get(url) as response:
                if response.status != 200:
                    raise ScrapingError(
                        f"Failed to fetch Premier League data: {response.status}"
                    )

                data = await response.json()
                return {
                    "id": data.get("id"),
                    "name": data.get("name"),
                    "code": data.get("code"),
                    "emblem": data.get("emblem"),
                    "current_season": data.get("currentSeason", {}),
                    "seasons": data.get("seasons", []),
                }

        except Exception as e:
            self.logger.error(f"Failed to get Premier League data: {e}")
            return {}

    async def _get_teams(self) -> List[Dict[str, Any]]:
        """Get Premier League teams."""
        try:
            url = f"{self.base_url}/competitions/PL/teams"

            async with self.session.get(url) as response:
                if response.status != 200:
                    self.logger.warning(f"Failed to fetch teams: {response.status}")
                    return []

                data = await response.json()
                teams = data.get("teams", [])

                return [
                    {
                        "id": team.get("id"),
                        "name": team.get("name"),
                        "short_name": team.get("shortName"),
                        "tla": team.get("tla"),
                        "crest": team.get("crest"),
                        "website": team.get("website"),
                        "founded": team.get("founded"),
                        "club_colors": team.get("clubColors"),
                        "venue": team.get("venue"),
                        "source": "football_data",
                    }
                    for team in teams
                ]

        except Exception as e:
            self.logger.error(f"Failed to get teams: {e}")
            return []

    async def _get_matches(self) -> List[Dict[str, Any]]:
        """Get Premier League matches."""
        try:
            url = f"{self.base_url}/competitions/PL/matches"

            async with self.session.get(url) as response:
                if response.status != 200:
                    self.logger.warning(f"Failed to fetch matches: {response.status}")
                    return []

                data = await response.json()
                matches = data.get("matches", [])

                return [
                    {
                        "id": match.get("id"),
                        "home_team": {
                            "id": match.get("homeTeam", {}).get("id"),
                            "name": match.get("homeTeam", {}).get("name"),
                            "short_name": match.get("homeTeam", {}).get("shortName"),
                            "tla": match.get("homeTeam", {}).get("tla"),
                            "crest": match.get("homeTeam", {}).get("crest"),
                        },
                        "away_team": {
                            "id": match.get("awayTeam", {}).get("id"),
                            "name": match.get("awayTeam", {}).get("name"),
                            "short_name": match.get("awayTeam", {}).get("shortName"),
                            "tla": match.get("awayTeam", {}).get("tla"),
                            "crest": match.get("awayTeam", {}).get("crest"),
                        },
                        "score": {
                            "full_time": {
                                "home": match.get("score", {})
                                .get("fullTime", {})
                                .get("home"),
                                "away": match.get("score", {})
                                .get("fullTime", {})
                                .get("away"),
                            },
                            "half_time": {
                                "home": match.get("score", {})
                                .get("halfTime", {})
                                .get("home"),
                                "away": match.get("score", {})
                                .get("halfTime", {})
                                .get("away"),
                            },
                        },
                        "status": match.get("status"),
                        "stage": match.get("stage"),
                        "group": match.get("group"),
                        "last_updated": match.get("lastUpdated"),
                        "utc_date": match.get("utcDate"),
                        "matchday": match.get("matchday"),
                        "season": match.get("season", {}),
                        "source": "football_data",
                    }
                    for match in matches
                ]

        except Exception as e:
            self.logger.error(f"Failed to get matches: {e}")
            return []

    async def _get_fixtures(self) -> List[Dict[str, Any]]:
        """Get Premier League fixtures."""
        try:
            # Get upcoming fixtures
            url = f"{self.base_url}/competitions/PL/matches?status=SCHEDULED"

            async with self.session.get(url) as response:
                if response.status != 200:
                    self.logger.warning(f"Failed to fetch fixtures: {response.status}")
                    return []

                data = await response.json()
                fixtures = data.get("matches", [])

                return [
                    {
                        "id": fixture.get("id"),
                        "home_team": {
                            "id": fixture.get("homeTeam", {}).get("id"),
                            "name": fixture.get("homeTeam", {}).get("name"),
                            "short_name": fixture.get("homeTeam", {}).get("shortName"),
                            "tla": fixture.get("homeTeam", {}).get("tla"),
                            "crest": fixture.get("homeTeam", {}).get("crest"),
                        },
                        "away_team": {
                            "id": fixture.get("awayTeam", {}).get("id"),
                            "name": fixture.get("awayTeam", {}).get("name"),
                            "short_name": fixture.get("awayTeam", {}).get("shortName"),
                            "tla": fixture.get("awayTeam", {}).get("tla"),
                            "crest": fixture.get("awayTeam", {}).get("crest"),
                        },
                        "status": fixture.get("status"),
                        "stage": fixture.get("stage"),
                        "group": fixture.get("group"),
                        "last_updated": fixture.get("lastUpdated"),
                        "utc_date": fixture.get("utcDate"),
                        "matchday": fixture.get("matchday"),
                        "season": fixture.get("season", {}),
                        "source": "football_data",
                    }
                    for fixture in fixtures
                ]

        except Exception as e:
            self.logger.error(f"Failed to get fixtures: {e}")
            return []

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate scraped Football-Data."""
        try:
            self.logger.info("Validating Football-Data")

            # Check required top-level keys
            required_keys = ["teams", "matches", "fixtures", "scraped_at", "source"]
            for key in required_keys:
                if key not in data:
                    self.logger.error(f"Missing required key: {key}")
                    return False

            # Validate teams data
            if not isinstance(data["teams"], list):
                self.logger.error("Teams data is not a list")
                return False

            # Validate matches data
            if not isinstance(data["matches"], list):
                self.logger.error("Matches data is not a list")
                return False

            # Validate fixtures data
            if not isinstance(data["fixtures"], list):
                self.logger.error("Fixtures data is not a list")
                return False

            # Check for reasonable data counts
            if len(data["teams"]) != 20:
                self.logger.warning(f"Expected 20 teams, found: {len(data['teams'])}")

            self.logger.info("Football-Data validation passed")
            return True

        except Exception as e:
            self.logger.error(f"Football-Data validation failed: {e}")
            return False
