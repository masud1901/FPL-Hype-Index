"""
Data validation utilities for the FPL Data Collection System.
"""

from typing import Dict, Any, List, Optional
from utils.logger import ProcessorLogger


class DataValidator:
    """Data validation utilities."""

    def __init__(self):
        """Initialize the data validator."""
        self.logger = ProcessorLogger("data_validator")

    async def validate(self, data: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Validate cleaned data.

        Args:
            data: Cleaned data to validate
            source: Source identifier

        Returns:
            Validation result with is_valid flag and issues list
        """
        try:
            self.logger.logger.info(
                "Starting data validation",
                processor=self.logger.processor_name,
                source=source,
            )

            issues = []

            # Validate based on source
            if source == "fpl_api":
                issues.extend(await self._validate_fpl_data(data))
            elif source == "understat":
                issues.extend(await self._validate_understat_data(data))
            elif source == "fbref":
                issues.extend(await self._validate_fbref_data(data))
            else:
                # Generic validation for unknown sources
                issues.extend(await self._validate_generic_data(data))

            is_valid = len(issues) == 0

            validation_result = {
                "is_valid": is_valid,
                "issues": issues,
                "source": source,
                "total_issues": len(issues),
            }

            self.logger.logger.info(
                "Data validation completed",
                processor=self.logger.processor_name,
                source=source,
                is_valid=is_valid,
                total_issues=len(issues),
            )

            return validation_result

        except Exception as e:
            self.logger.logger.error(
                "Data validation failed",
                processor=self.logger.processor_name,
                source=source,
                error=str(e),
            )
            return {
                "is_valid": False,
                "issues": [f"Validation error: {str(e)}"],
                "source": source,
                "total_issues": 1,
            }

    async def _validate_fpl_data(self, data: Dict[str, Any]) -> List[str]:
        """Validate FPL API data.

        Args:
            data: FPL API data

        Returns:
            List of validation issues
        """
        issues = []

        # Check required top-level keys
        required_keys = ["players", "teams", "gameweeks", "scraped_at", "source"]
        for key in required_keys:
            if key not in data:
                issues.append(f"Missing required key: {key}")

        # Validate players data
        if "players" in data:
            player_issues = self._validate_players_data(data["players"])
            issues.extend(player_issues)

        # Validate teams data
        if "teams" in data:
            team_issues = self._validate_teams_data(data["teams"])
            issues.extend(team_issues)

        # Validate gameweeks data
        if "gameweeks" in data:
            gameweek_issues = self._validate_gameweeks_data(data["gameweeks"])
            issues.extend(gameweek_issues)

        return issues

    def _validate_players_data(self, players: List[Dict[str, Any]]) -> List[str]:
        """Validate players data.

        Args:
            players: List of player data

        Returns:
            List of validation issues
        """
        issues = []

        if not isinstance(players, list):
            issues.append("Players data is not a list")
            return issues

        if len(players) == 0:
            issues.append("No players data found")
            return issues

        # Check for reasonable number of players (Premier League has ~500-600 players)
        if len(players) < 400 or len(players) > 700:
            issues.append(f"Unusual number of players: {len(players)}")

        # Validate individual players
        required_player_fields = [
            "id",
            "first_name",
            "second_name",
            "team",
            "element_type",
        ]

        for i, player in enumerate(players):
            if not isinstance(player, dict):
                issues.append(f"Player {i} is not a dictionary")
                continue

            # Check required fields
            for field in required_player_fields:
                if field not in player:
                    issues.append(f"Player {i} missing required field: {field}")

            # Validate field types and ranges
            if "id" in player and not isinstance(player["id"], int):
                issues.append(f"Player {i} has invalid ID type: {type(player['id'])}")

            if "element_type" in player:
                element_type = player["element_type"]
                if not isinstance(element_type, int) or element_type not in [
                    1,
                    2,
                    3,
                    4,
                ]:
                    issues.append(
                        f"Player {i} has invalid element_type: {element_type}"
                    )

            if "now_cost" in player:
                cost = player["now_cost"]
                if (
                    not isinstance(cost, int) or cost < 0 or cost > 1500
                ):  # Max reasonable price
                    issues.append(f"Player {i} has invalid cost: {cost}")

            if "total_points" in player:
                points = player["total_points"]
                if (
                    not isinstance(points, int) or points < -100
                ):  # Allow negative points (red cards, own goals, etc.)
                    issues.append(f"Player {i} has invalid total_points: {points}")

        return issues

    def _validate_teams_data(self, teams: List[Dict[str, Any]]) -> List[str]:
        """Validate teams data.

        Args:
            teams: List of team data

        Returns:
            List of validation issues
        """
        issues = []

        if not isinstance(teams, list):
            issues.append("Teams data is not a list")
            return issues

        if len(teams) == 0:
            issues.append("No teams data found")
            return issues

        # Check for exactly 20 teams (Premier League)
        if len(teams) != 20:
            issues.append(f"Expected 20 teams, found: {len(teams)}")

        # Validate individual teams
        required_team_fields = ["id", "name", "short_name", "code"]

        for i, team in enumerate(teams):
            if not isinstance(team, dict):
                issues.append(f"Team {i} is not a dictionary")
                continue

            # Check required fields
            for field in required_team_fields:
                if field not in team:
                    issues.append(f"Team {i} missing required field: {field}")

            # Validate field types
            if "id" in team and not isinstance(team["id"], int):
                issues.append(f"Team {i} has invalid ID type: {type(team['id'])}")

            if "code" in team and not isinstance(team["code"], int):
                issues.append(f"Team {i} has invalid code type: {type(team['code'])}")

        return issues

    def _validate_gameweeks_data(self, gameweeks: List[Dict[str, Any]]) -> List[str]:
        """Validate gameweeks data.

        Args:
            gameweeks: List of gameweek data

        Returns:
            List of validation issues
        """
        issues = []

        if not isinstance(gameweeks, list):
            issues.append("Gameweeks data is not a list")
            return issues

        if len(gameweeks) == 0:
            issues.append("No gameweeks data found")
            return issues

        # Check for reasonable number of gameweeks (38 in a season)
        if len(gameweeks) < 30 or len(gameweeks) > 40:
            issues.append(f"Unusual number of gameweeks: {len(gameweeks)}")

        # Validate individual gameweeks
        required_gameweek_fields = [
            "id",
            "name",
            "deadline_time",
            "finished",
            "data_checked",
        ]

        for i, gameweek in enumerate(gameweeks):
            if not isinstance(gameweek, dict):
                issues.append(f"Gameweek {i} is not a dictionary")
                continue

            # Check required fields
            for field in required_gameweek_fields:
                if field not in gameweek:
                    issues.append(f"Gameweek {i} missing required field: {field}")

            # Validate field types
            if "id" in gameweek and not isinstance(gameweek["id"], int):
                issues.append(
                    f"Gameweek {i} has invalid ID type: {type(gameweek['id'])}"
                )

            if "finished" in gameweek and not isinstance(gameweek["finished"], bool):
                issues.append(
                    f"Gameweek {i} has invalid finished type: {type(gameweek['finished'])}"
                )

        return issues

    async def _validate_understat_data(self, data: Dict[str, Any]) -> List[str]:
        """Validate Understat data.

        Args:
            data: Understat data

        Returns:
            List of validation issues
        """
        # Placeholder for Understat data validation
        # Will be implemented when Understat scraper is added
        return []

    async def _validate_fbref_data(self, data: Dict[str, Any]) -> List[str]:
        """Validate FBRef data.

        Args:
            data: FBRef data

        Returns:
            List of validation issues
        """
        # Placeholder for FBRef data validation
        # Will be implemented when FBRef scraper is added
        return []

    async def _validate_generic_data(self, data: Dict[str, Any]) -> List[str]:
        """Generic data validation for unknown sources.

        Args:
            data: Generic data

        Returns:
            List of validation issues
        """
        issues = []

        if not isinstance(data, dict):
            issues.append("Data is not a dictionary")
            return issues

        if len(data) == 0:
            issues.append("Data is empty")
            return issues

        # Basic validation for common data types
        for key, value in data.items():
            if value is None:
                issues.append(f"Key '{key}' has null value")
            elif isinstance(value, str) and len(value.strip()) == 0:
                issues.append(f"Key '{key}' has empty string value")

        return issues
