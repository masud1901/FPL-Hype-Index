"""
Data cleaning utilities for the FPL Data Collection System.
"""
import re
from typing import Dict, Any, List, Optional
from utils.logger import ProcessorLogger


class DataCleaner:
    """Data cleaning and normalization utilities."""
    
    def __init__(self):
        """Initialize the data cleaner."""
        self.logger = ProcessorLogger("data_cleaner")
    
    async def clean(self, data: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Clean and normalize scraped data.
        
        Args:
            data: Raw scraped data
            source: Source identifier
            
        Returns:
            Cleaned data
        """
        try:
            self.logger.logger.info(
                "Starting data cleaning",
                processor=self.logger.processor_name,
                source=source
            )
            
            cleaned_data = data.copy()
            
            # Clean based on source
            if source == 'fpl_api':
                cleaned_data = await self._clean_fpl_data(cleaned_data)
            elif source == 'understat':
                cleaned_data = await self._clean_understat_data(cleaned_data)
            elif source == 'fbref':
                cleaned_data = await self._clean_fbref_data(cleaned_data)
            else:
                # Generic cleaning for unknown sources
                cleaned_data = await self._clean_generic_data(cleaned_data)
            
            self.logger.logger.info(
                "Data cleaning completed",
                processor=self.logger.processor_name,
                source=source
            )
            
            return cleaned_data
            
        except Exception as e:
            self.logger.logger.error(
                "Data cleaning failed",
                processor=self.logger.processor_name,
                source=source,
                error=str(e)
            )
            raise
    
    async def _clean_fpl_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean FPL API data.
        
        Args:
            data: FPL API data
            
        Returns:
            Cleaned FPL data
        """
        cleaned_data = data.copy()
        
        # Clean players data
        if 'players' in cleaned_data:
            cleaned_players = []
            for player in cleaned_data['players']:
                cleaned_player = self._clean_player_data(player)
                if cleaned_player:
                    cleaned_players.append(cleaned_player)
            cleaned_data['players'] = cleaned_players
        
        # Clean teams data
        if 'teams' in cleaned_data:
            cleaned_teams = []
            for team in cleaned_data['teams']:
                cleaned_team = self._clean_team_data(team)
                if cleaned_team:
                    cleaned_teams.append(cleaned_team)
            cleaned_data['teams'] = cleaned_teams
        
        return cleaned_data
    
    def _clean_player_data(self, player: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Clean individual player data.
        
        Args:
            player: Player data
            
        Returns:
            Cleaned player data or None if invalid
        """
        if not isinstance(player, dict):
            return None
        
        cleaned_player = player.copy()
        
        # Clean name fields
        if 'first_name' in cleaned_player:
            cleaned_player['first_name'] = self._clean_string(cleaned_player['first_name'])
        if 'second_name' in cleaned_player:
            cleaned_player['second_name'] = self._clean_string(cleaned_player['second_name'])
        if 'web_name' in cleaned_player:
            cleaned_player['web_name'] = self._clean_string(cleaned_player['web_name'])
        
        # Convert numeric fields
        numeric_fields = [
            'id', 'team', 'element_type', 'now_cost', 'total_points',
            'goals_scored', 'assists', 'clean_sheets', 'goals_conceded',
            'own_goals', 'penalties_saved', 'penalties_missed',
            'yellow_cards', 'red_cards', 'saves', 'bonus', 'bps',
            'transfers_in', 'transfers_out'
        ]
        
        for field in numeric_fields:
            if field in cleaned_player:
                cleaned_player[field] = self._convert_to_int(cleaned_player[field])
        
        # Convert float fields
        float_fields = ['selected_by_percent', 'form', 'influence', 'creativity', 'threat', 'ict_index']
        for field in float_fields:
            if field in cleaned_player:
                cleaned_player[field] = self._convert_to_float(cleaned_player[field])
        
        return cleaned_player
    
    def _clean_team_data(self, team: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Clean individual team data.
        
        Args:
            team: Team data
            
        Returns:
            Cleaned team data or None if invalid
        """
        if not isinstance(team, dict):
            return None
        
        cleaned_team = team.copy()
        
        # Clean name fields
        if 'name' in cleaned_team:
            cleaned_team['name'] = self._clean_string(cleaned_team['name'])
        if 'short_name' in cleaned_team:
            cleaned_team['short_name'] = self._clean_string(cleaned_team['short_name'])
        
        # Convert numeric fields
        numeric_fields = ['id', 'code']
        for field in numeric_fields:
            if field in cleaned_team:
                cleaned_team[field] = self._convert_to_int(cleaned_team[field])
        
        return cleaned_team
    
    async def _clean_understat_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean Understat data.
        
        Args:
            data: Understat data
            
        Returns:
            Cleaned Understat data
        """
        # Placeholder for Understat data cleaning
        # Will be implemented when Understat scraper is added
        return data
    
    async def _clean_fbref_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean FBRef data.
        
        Args:
            data: FBRef data
            
        Returns:
            Cleaned FBRef data
        """
        # Placeholder for FBRef data cleaning
        # Will be implemented when FBRef scraper is added
        return data
    
    async def _clean_generic_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generic data cleaning for unknown sources.
        
        Args:
            data: Generic data
            
        Returns:
            Cleaned data
        """
        # Basic string cleaning for all string values
        if isinstance(data, dict):
            cleaned_data = {}
            for key, value in data.items():
                if isinstance(value, str):
                    cleaned_data[key] = self._clean_string(value)
                elif isinstance(value, dict):
                    cleaned_data[key] = await self._clean_generic_data(value)
                elif isinstance(value, list):
                    cleaned_data[key] = [
                        await self._clean_generic_data(item) if isinstance(item, dict)
                        else self._clean_string(item) if isinstance(item, str)
                        else item
                        for item in value
                    ]
                else:
                    cleaned_data[key] = value
            return cleaned_data
        elif isinstance(data, str):
            return self._clean_string(data)
        else:
            return data
    
    def _clean_string(self, value: Any) -> str:
        """Clean a string value.
        
        Args:
            value: Value to clean
            
        Returns:
            Cleaned string
        """
        if not isinstance(value, str):
            return str(value) if value is not None else ""
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', value.strip())
        
        # Remove null characters
        cleaned = cleaned.replace('\x00', '')
        
        return cleaned
    
    def _convert_to_int(self, value: Any) -> int:
        """Convert value to integer.
        
        Args:
            value: Value to convert
            
        Returns:
            Integer value
        """
        if value is None:
            return 0
        
        try:
            # Handle string percentages (e.g., "12.5%")
            if isinstance(value, str) and '%' in value:
                return int(float(value.replace('%', '')))
            
            return int(float(value))
        except (ValueError, TypeError):
            return 0
    
    def _convert_to_float(self, value: Any) -> float:
        """Convert value to float.
        
        Args:
            value: Value to convert
            
        Returns:
            Float value
        """
        if value is None:
            return 0.0
        
        try:
            # Handle string percentages (e.g., "12.5%")
            if isinstance(value, str) and '%' in value:
                return float(value.replace('%', ''))
            
            return float(value)
        except (ValueError, TypeError):
            return 0.0 