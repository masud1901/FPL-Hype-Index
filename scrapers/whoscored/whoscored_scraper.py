"""
WhoScored scraper for FPL Data Collection System.

This scraper collects:
- Player performance ratings
- Match statistics
- Team performance metrics
- Detailed player stats
- Form analysis
"""

import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import json
import re
from bs4 import BeautifulSoup
import time

from scrapers.base.base_scraper import BaseScraper
from scrapers.base.exceptions import ScrapingError, ValidationError
from .models import WhoScoredPlayer, WhoScoredTeam, WhoScoredMatch
from utils.logger import get_logger


class WhoScoredScraper(BaseScraper):
    """WhoScored scraper for performance ratings and match statistics."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the WhoScored scraper."""
        super().__init__(config)
        self.logger = get_logger(__name__)
        self.base_url = "https://www.whoscored.com"
        self.session = None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    async def scrape(self) -> Dict[str, Any]:
        """Main scraping method for WhoScored data."""
        try:
            self.logger.info("Starting WhoScored data collection")

            # Initialize session
            self.session = aiohttp.ClientSession(headers=self.headers)

            # Get Premier League teams
            teams = await self._get_premier_league_teams()
            self.logger.info(f"Found {len(teams)} Premier League teams")

            # Collect data for each team
            all_players = []
            all_matches = []
            team_data = []

            for team in teams:
                self.logger.info(f"Processing team: {team['name']}")

                # Get team players
                team_players = await self._get_team_players(team["url"])
                all_players.extend(team_players)

                # Get team matches
                team_matches = await self._get_team_matches(team["url"])
                all_matches.extend(team_matches)

                # Add team data
                team_data.append(team)

                # Rate limiting
                await asyncio.sleep(3)

            # Compile final data
            scraped_data = {
                "players": all_players,
                "teams": team_data,
                "matches": all_matches,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "source": "whoscored",
                "season": "2024/25",
                "league": "Premier League",
            }

            self.logger.info(
                "WhoScored scraping completed",
                players_count=len(all_players),
                teams_count=len(team_data),
                matches_count=len(all_matches),
            )

            return scraped_data

        except Exception as e:
            self.logger.error(f"WhoScored scraping failed: {e}")
            raise ScrapingError(f"Failed to scrape WhoScored: {str(e)}")

        finally:
            if self.session:
                await self.session.close()

    async def _get_premier_league_teams(self) -> List[Dict[str, Any]]:
        """Get Premier League teams from WhoScored."""
        try:
            url = f"{self.base_url}/Regions/252/Tournaments/2/England-Premier-League"

            async with self.session.get(url) as response:
                if response.status != 200:
                    raise ScrapingError(
                        f"Failed to fetch teams page: {response.status}"
                    )

                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                teams = []
                team_links = soup.find_all("a", href=re.compile(r"/Teams/"))

                for link in team_links:
                    try:
                        team_name = link.get_text(strip=True)
                        team_url = self.base_url + link.get("href", "")
                        team_id = self._extract_id_from_url(team_url)

                        if team_name and team_id:
                            teams.append(
                                {
                                    "id": team_id,
                                    "name": team_name,
                                    "url": team_url,
                                    "league": "Premier League",
                                    "season": "2024/25",
                                }
                            )

                    except Exception as e:
                        self.logger.warning(f"Failed to parse team link: {e}")
                        continue

                return teams[:20]  # Limit to 20 teams

        except Exception as e:
            self.logger.error(f"Failed to get Premier League teams: {e}")
            raise

    async def _get_team_players(self, team_url: str) -> List[Dict[str, Any]]:
        """Get players for a specific team."""
        try:
            # Navigate to team's squad page
            squad_url = team_url + "/Squad"

            async with self.session.get(squad_url) as response:
                if response.status != 200:
                    self.logger.warning(
                        f"Failed to fetch squad page for {team_url}: {response.status}"
                    )
                    return []

                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                players = []
                player_rows = soup.find_all("tr", class_="row")

                for row in player_rows:
                    try:
                        player_data = self._parse_player_row(row)
                        if player_data:
                            players.append(player_data)

                    except Exception as e:
                        self.logger.warning(f"Failed to parse player row: {e}")
                        continue

                return players

        except Exception as e:
            self.logger.error(f"Failed to get team players for {team_url}: {e}")
            return []

    def _parse_player_row(self, row) -> Optional[Dict[str, Any]]:
        """Parse a player row from the team squad table."""
        try:
            cells = row.find_all("td")
            if len(cells) < 5:
                return None

            # Player name and URL
            name_cell = cells[0]
            name_link = name_cell.find("a")
            if not name_link:
                return None

            player_name = name_link.get_text(strip=True)
            player_url = self.base_url + name_link.get("href", "")
            player_id = self._extract_id_from_url(player_url)

            # Position
            position = cells[1].get_text(strip=True) if len(cells) > 1 else ""

            # Age
            age_text = cells[2].get_text(strip=True) if len(cells) > 2 else "0"
            age = int(age_text) if age_text.isdigit() else 0

            # Rating
            rating_cell = cells[3] if len(cells) > 3 else None
            rating = (
                self._parse_rating(rating_cell.get_text(strip=True))
                if rating_cell
                else 0.0
            )

            # Appearances
            apps_cell = cells[4] if len(cells) > 4 else None
            appearances = (
                int(apps_cell.get_text(strip=True))
                if apps_cell and apps_cell.get_text(strip=True).isdigit()
                else 0
            )

            return {
                "id": player_id,
                "name": player_name,
                "url": player_url,
                "position": position,
                "age": age,
                "rating": rating,
                "appearances": appearances,
                "source": "whoscored",
            }

        except Exception as e:
            self.logger.warning(f"Failed to parse player row: {e}")
            return None

    def _parse_rating(self, rating_text: str) -> float:
        """Parse rating from WhoScored format."""
        try:
            if not rating_text or rating_text == "-":
                return 0.0

            # Extract numeric value
            numeric_value = re.search(r"[\d.]+", rating_text)
            if numeric_value:
                rating = float(numeric_value.group())
                # WhoScored ratings are typically out of 10
                return min(max(rating, 0.0), 10.0)

            return 0.0

        except Exception as e:
            self.logger.warning(f"Failed to parse rating '{rating_text}': {e}")
            return 0.0

    async def _get_team_matches(self, team_url: str) -> List[Dict[str, Any]]:
        """Get match history for a specific team."""
        try:
            # Navigate to team's fixtures page
            fixtures_url = team_url + "/Fixtures"

            async with self.session.get(fixtures_url) as response:
                if response.status != 200:
                    self.logger.warning(
                        f"Failed to fetch fixtures page for {team_url}: {response.status}"
                    )
                    return []

                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                matches = []
                match_rows = soup.find_all("tr", class_="row")

                for row in match_rows:
                    try:
                        match_data = self._parse_match_row(row)
                        if match_data:
                            matches.append(match_data)

                    except Exception as e:
                        self.logger.warning(f"Failed to parse match row: {e}")
                        continue

                return matches

        except Exception as e:
            self.logger.error(f"Failed to get team matches for {team_url}: {e}")
            return []

    def _parse_match_row(self, row) -> Optional[Dict[str, Any]]:
        """Parse a match row from the fixtures table."""
        try:
            cells = row.find_all("td")
            if len(cells) < 6:
                return None

            # Date
            date_cell = cells[0]
            match_date = date_cell.get_text(strip=True) if date_cell else ""

            # Home team
            home_cell = cells[1]
            home_team = home_cell.get_text(strip=True) if home_cell else ""

            # Score
            score_cell = cells[2]
            score_text = score_cell.get_text(strip=True) if score_cell else ""
            home_score, away_score = self._parse_score(score_text)

            # Away team
            away_cell = cells[3]
            away_team = away_cell.get_text(strip=True) if away_cell else ""

            # Competition
            comp_cell = cells[4] if len(cells) > 4 else None
            competition = comp_cell.get_text(strip=True) if comp_cell else ""

            # Result
            result_cell = cells[5] if len(cells) > 5 else None
            result = result_cell.get_text(strip=True) if result_cell else ""

            return {
                "date": match_date,
                "home_team": home_team,
                "away_team": away_team,
                "home_score": home_score,
                "away_score": away_score,
                "competition": competition,
                "result": result,
                "source": "whoscored",
            }

        except Exception as e:
            self.logger.warning(f"Failed to parse match row: {e}")
            return None

    def _parse_score(self, score_text: str) -> tuple:
        """Parse score from match result."""
        try:
            if not score_text or score_text == "-":
                return 0, 0

            # Extract scores from format like "2-1" or "0-0"
            score_match = re.search(r"(\d+)-(\d+)", score_text)
            if score_match:
                home_score = int(score_match.group(1))
                away_score = int(score_match.group(2))
                return home_score, away_score

            return 0, 0

        except Exception as e:
            self.logger.warning(f"Failed to parse score '{score_text}': {e}")
            return 0, 0

    def _extract_id_from_url(self, url: str) -> str:
        """Extract ID from WhoScored URL."""
        try:
            # Extract ID from URL patterns like /Players/12345/ or /Teams/12345/
            match = re.search(r"/(\d+)/", url)
            return match.group(1) if match else ""
        except Exception:
            return ""

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate scraped WhoScored data."""
        try:
            self.logger.info("Validating WhoScored data")

            # Check required top-level keys
            required_keys = ["players", "teams", "matches", "scraped_at", "source"]
            for key in required_keys:
                if key not in data:
                    self.logger.error(f"Missing required key: {key}")
                    return False

            # Validate players data
            if not isinstance(data["players"], list):
                self.logger.error("Players data is not a list")
                return False

            # Validate teams data
            if not isinstance(data["teams"], list):
                self.logger.error("Teams data is not a list")
                return False

            # Validate matches data
            if not isinstance(data["matches"], list):
                self.logger.error("Matches data is not a list")
                return False

            # Check for reasonable data counts
            if len(data["players"]) < 100:
                self.logger.warning(f"Low player count: {len(data['players'])}")

            if len(data["teams"]) != 20:
                self.logger.warning(f"Expected 20 teams, found: {len(data['teams'])}")

            self.logger.info("WhoScored data validation passed")
            return True

        except Exception as e:
            self.logger.error(f"WhoScored data validation failed: {e}")
            return False
