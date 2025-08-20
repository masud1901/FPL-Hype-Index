"""
Transfermarkt scraper for FPL Data Collection System.

This scraper collects:
- Player market values
- Transfer history
- Injury information
- Contract details
- Performance ratings
"""

import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import re
from bs4 import BeautifulSoup
import time

from scrapers.base.base_scraper import BaseScraper
from scrapers.base.exceptions import ScrapingError, ValidationError
from .models import TransfermarktPlayer, TransfermarktTeam, TransfermarktTransfer
from utils.logger import get_logger


class TransfermarktScraper(BaseScraper):
    """Transfermarkt scraper for market data and transfer information."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the Transfermarkt scraper."""
        super().__init__(config)
        self.logger = get_logger(__name__)
        self.base_url = "https://www.transfermarkt.com"
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
        """Main scraping method for Transfermarkt data."""
        try:
            self.logger.info("Starting Transfermarkt data collection")

            # Initialize session
            self.session = aiohttp.ClientSession(headers=self.headers)

            # Get Premier League teams
            teams = await self._get_premier_league_teams()
            self.logger.info(f"Found {len(teams)} Premier League teams")

            # Collect data for each team
            all_players = []
            all_transfers = []
            team_data = []

            for team in teams:
                self.logger.info(f"Processing team: {team['name']}")

                # Get team players
                team_players = await self._get_team_players(team["url"])
                all_players.extend(team_players)

                # Get team transfers
                team_transfers = await self._get_team_transfers(team["url"])
                all_transfers.extend(team_transfers)

                # Add team data
                team_data.append(team)

                # Rate limiting
                await asyncio.sleep(2)

            # Compile final data
            scraped_data = {
                "players": all_players,
                "teams": team_data,
                "transfers": all_transfers,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "source": "transfermarkt",
                "season": "2024/25",
                "league": "Premier League",
            }

            self.logger.info(
                "Transfermarkt scraping completed",
                players_count=len(all_players),
                teams_count=len(team_data),
                transfers_count=len(all_transfers),
            )

            return scraped_data

        except Exception as e:
            self.logger.error(f"Transfermarkt scraping failed: {e}")
            raise ScrapingError(f"Failed to scrape Transfermarkt: {str(e)}")

        finally:
            if self.session:
                await self.session.close()

    async def _get_premier_league_teams(self) -> List[Dict[str, Any]]:
        """Get Premier League teams from Transfermarkt."""
        try:
            url = f"{self.base_url}/premier-league/startseite/wettbewerb/GB1"

            async with self.session.get(url) as response:
                if response.status != 200:
                    raise ScrapingError(
                        f"Failed to fetch teams page: {response.status}"
                    )

                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                teams = []
                team_rows = soup.find_all("tr", class_="odd") + soup.find_all(
                    "tr", class_="even"
                )

                for row in team_rows:
                    try:
                        name_cell = row.find("td", class_="hauptlink")
                        if not name_cell:
                            continue

                        name_link = name_cell.find("a")
                        if not name_link:
                            continue

                        team_name = name_link.get_text(strip=True)
                        team_url = self.base_url + name_link.get("href", "")
                        team_id = self._extract_id_from_url(team_url)

                        # Get additional team info
                        squad_size_cell = (
                            row.find_all("td")[2]
                            if len(row.find_all("td")) > 2
                            else None
                        )
                        squad_size = (
                            int(squad_size_cell.get_text(strip=True))
                            if squad_size_cell
                            else 0
                        )

                        teams.append(
                            {
                                "id": team_id,
                                "name": team_name,
                                "url": team_url,
                                "squad_size": squad_size,
                                "league": "Premier League",
                                "season": "2024/25",
                            }
                        )

                    except Exception as e:
                        self.logger.warning(f"Failed to parse team row: {e}")
                        continue

                return teams

        except Exception as e:
            self.logger.error(f"Failed to get Premier League teams: {e}")
            raise

    async def _get_team_players(self, team_url: str) -> List[Dict[str, Any]]:
        """Get players for a specific team."""
        try:
            # Navigate to team's squad page
            squad_url = team_url.replace("/startseite/", "/kader/")

            async with self.session.get(squad_url) as response:
                if response.status != 200:
                    self.logger.warning(
                        f"Failed to fetch squad page for {team_url}: {response.status}"
                    )
                    return []

                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                players = []
                player_rows = soup.find_all("tr", class_="odd") + soup.find_all(
                    "tr", class_="even"
                )

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
            if len(cells) < 8:
                return None

            # Player name and URL
            name_cell = cells[1]
            name_link = name_cell.find("a")
            if not name_link:
                return None

            player_name = name_link.get_text(strip=True)
            player_url = self.base_url + name_link.get("href", "")
            player_id = self._extract_id_from_url(player_url)

            # Position
            position = cells[2].get_text(strip=True) if len(cells) > 2 else ""

            # Age
            age_text = cells[3].get_text(strip=True) if len(cells) > 3 else "0"
            age = int(age_text) if age_text.isdigit() else 0

            # Market value
            market_value_cell = cells[4] if len(cells) > 4 else None
            market_value = (
                self._parse_market_value(market_value_cell.get_text(strip=True))
                if market_value_cell
                else 0
            )

            # Contract until
            contract_cell = cells[5] if len(cells) > 5 else None
            contract_until = contract_cell.get_text(strip=True) if contract_cell else ""

            # Last club
            last_club_cell = cells[6] if len(cells) > 6 else None
            last_club = last_club_cell.get_text(strip=True) if last_club_cell else ""

            return {
                "id": player_id,
                "name": player_name,
                "url": player_url,
                "position": position,
                "age": age,
                "market_value": market_value,
                "contract_until": contract_until,
                "last_club": last_club,
                "source": "transfermarkt",
            }

        except Exception as e:
            self.logger.warning(f"Failed to parse player row: {e}")
            return None

    def _parse_market_value(self, value_text: str) -> float:
        """Parse market value from Transfermarkt format."""
        try:
            if not value_text or value_text == "-":
                return 0.0

            # Remove currency symbols and spaces
            clean_text = re.sub(r"[€£$,\s]", "", value_text)

            # Handle multipliers (k = thousands, m = millions)
            multiplier = 1
            if "k" in clean_text.lower():
                multiplier = 1000
                clean_text = clean_text.lower().replace("k", "")
            elif "m" in clean_text.lower():
                multiplier = 1000000
                clean_text = clean_text.lower().replace("m", "")

            # Extract numeric value
            numeric_value = re.search(r"[\d.]+", clean_text)
            if numeric_value:
                return float(numeric_value.group()) * multiplier

            return 0.0

        except Exception as e:
            self.logger.warning(f"Failed to parse market value '{value_text}': {e}")
            return 0.0

    async def _get_team_transfers(self, team_url: str) -> List[Dict[str, Any]]:
        """Get transfer history for a specific team."""
        try:
            # Navigate to team's transfers page
            transfers_url = team_url.replace("/startseite/", "/transfers/")

            async with self.session.get(transfers_url) as response:
                if response.status != 200:
                    self.logger.warning(
                        f"Failed to fetch transfers page for {team_url}: {response.status}"
                    )
                    return []

                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                transfers = []
                transfer_rows = soup.find_all("tr", class_="odd") + soup.find_all(
                    "tr", class_="even"
                )

                for row in transfer_rows:
                    try:
                        transfer_data = self._parse_transfer_row(row)
                        if transfer_data:
                            transfers.append(transfer_data)

                    except Exception as e:
                        self.logger.warning(f"Failed to parse transfer row: {e}")
                        continue

                return transfers

        except Exception as e:
            self.logger.error(f"Failed to get team transfers for {team_url}: {e}")
            return []

    def _parse_transfer_row(self, row) -> Optional[Dict[str, Any]]:
        """Parse a transfer row from the transfers table."""
        try:
            cells = row.find_all("td")
            if len(cells) < 6:
                return None

            # Player name
            player_cell = cells[0]
            player_link = player_cell.find("a")
            player_name = player_link.get_text(strip=True) if player_link else ""

            # Position
            position = cells[1].get_text(strip=True) if len(cells) > 1 else ""

            # Age
            age_text = cells[2].get_text(strip=True) if len(cells) > 2 else "0"
            age = int(age_text) if age_text.isdigit() else 0

            # Transfer type (in/out)
            transfer_type = cells[3].get_text(strip=True) if len(cells) > 3 else ""

            # Fee
            fee_cell = cells[4] if len(cells) > 4 else None
            fee = (
                self._parse_market_value(fee_cell.get_text(strip=True))
                if fee_cell
                else 0
            )

            # Date
            date_cell = cells[5] if len(cells) > 5 else None
            transfer_date = date_cell.get_text(strip=True) if date_cell else ""

            return {
                "player_name": player_name,
                "position": position,
                "age": age,
                "transfer_type": transfer_type,
                "fee": fee,
                "date": transfer_date,
                "source": "transfermarkt",
            }

        except Exception as e:
            self.logger.warning(f"Failed to parse transfer row: {e}")
            return None

    def _extract_id_from_url(self, url: str) -> str:
        """Extract ID from Transfermarkt URL."""
        try:
            # Extract ID from URL patterns like /spieler/12345/ or /verein/12345/
            match = re.search(r"/(\d+)/", url)
            return match.group(1) if match else ""
        except Exception:
            return ""

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate scraped Transfermarkt data."""
        try:
            self.logger.info("Validating Transfermarkt data")

            # Check required top-level keys
            required_keys = ["players", "teams", "transfers", "scraped_at", "source"]
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

            # Validate transfers data
            if not isinstance(data["transfers"], list):
                self.logger.error("Transfers data is not a list")
                return False

            # Check for reasonable data counts
            if len(data["players"]) < 100:
                self.logger.warning(f"Low player count: {len(data['players'])}")

            if len(data["teams"]) != 20:
                self.logger.warning(f"Expected 20 teams, found: {len(data['teams'])}")

            self.logger.info("Transfermarkt data validation passed")
            return True

        except Exception as e:
            self.logger.error(f"Transfermarkt data validation failed: {e}")
            return False
