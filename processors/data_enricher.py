"""
Data enrichment utilities for the FPL Data Collection System.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from utils.logger import ProcessorLogger


class DataEnricher:
    """Data enrichment utilities."""
    
    def __init__(self):
        """Initialize the data enricher."""
        self.logger = ProcessorLogger("data_enricher")
    
    async def enrich(self, data: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Enrich cleaned and validated data with additional context.
        
        Args:
            data: Cleaned and validated data
            source: Source identifier
            
        Returns:
            Enriched data
        """
        try:
            self.logger.logger.info(
                "Starting data enrichment",
                processor=self.logger.processor_name,
                source=source
            )
            
            enriched_data = data.copy()
            
            # Enrich based on source
            if source == 'fpl_api':
                enriched_data = await self._enrich_fpl_data(enriched_data)
            elif source == 'understat':
                enriched_data = await self._enrich_understat_data(enriched_data)
            elif source == 'fbref':
                enriched_data = await self._enrich_fbref_data(enriched_data)
            else:
                # Generic enrichment for unknown sources
                enriched_data = await self._enrich_generic_data(enriched_data)
            
            # Add common enrichment
            enriched_data = await self._add_common_enrichment(enriched_data, source)
            
            self.logger.logger.info(
                "Data enrichment completed",
                processor=self.logger.processor_name,
                source=source
            )
            
            return enriched_data
            
        except Exception as e:
            self.logger.logger.error(
                "Data enrichment failed",
                processor=self.logger.processor_name,
                source=source,
                error=str(e)
            )
            raise
    
    async def _enrich_fpl_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich FPL API data.
        
        Args:
            data: FPL API data
            
        Returns:
            Enriched FPL data
        """
        enriched_data = data.copy()
        
        # Enrich players data
        if 'players' in enriched_data:
            enriched_players = []
            for player in enriched_data['players']:
                enriched_player = self._enrich_player_data(player)
                enriched_players.append(enriched_player)
            enriched_data['players'] = enriched_players
        
        # Enrich teams data
        if 'teams' in enriched_data:
            enriched_teams = []
            for team in enriched_data['teams']:
                enriched_team = self._enrich_team_data(team)
                enriched_teams.append(enriched_team)
            enriched_data['teams'] = enriched_teams
        
        # Add team mapping for players
        if 'players' in enriched_data and 'teams' in enriched_data:
            team_map = {team['id']: team for team in enriched_data['teams']}
            for player in enriched_data['players']:
                if 'team' in player and player['team'] in team_map:
                    player['team_name'] = team_map[player['team']]['name']
                    player['team_short_name'] = team_map[player['team']]['short_name']
        
        return enriched_data
    
    def _enrich_player_data(self, player: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich individual player data.
        
        Args:
            player: Player data
            
        Returns:
            Enriched player data
        """
        enriched_player = player.copy()
        
        # Add computed fields
        if 'first_name' in enriched_player and 'second_name' in enriched_player:
            enriched_player['full_name'] = f"{enriched_player['first_name']} {enriched_player['second_name']}"
        
        # Add position mapping
        if 'element_type' in enriched_player:
            position_map = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}
            enriched_player['position'] = position_map.get(enriched_player['element_type'], "UNK")
        
        # Add price in pounds
        if 'now_cost' in enriched_player:
            enriched_player['price'] = enriched_player['now_cost'] / 10.0
        
        # Add form as float
        if 'form' in enriched_player:
            try:
                enriched_player['form_float'] = float(enriched_player['form'])
            except (ValueError, TypeError):
                enriched_player['form_float'] = 0.0
        
        # Add ICT index as float
        if 'ict_index' in enriched_player:
            try:
                enriched_player['ict_index_float'] = float(enriched_player['ict_index'])
            except (ValueError, TypeError):
                enriched_player['ict_index_float'] = 0.0
        
        # Add influence as float
        if 'influence' in enriched_player:
            try:
                enriched_player['influence_float'] = float(enriched_player['influence'])
            except (ValueError, TypeError):
                enriched_player['influence_float'] = 0.0
        
        # Add creativity as float
        if 'creativity' in enriched_player:
            try:
                enriched_player['creativity_float'] = float(enriched_player['creativity'])
            except (ValueError, TypeError):
                enriched_player['creativity_float'] = 0.0
        
        # Add threat as float
        if 'threat' in enriched_player:
            try:
                enriched_player['threat_float'] = float(enriched_player['threat'])
            except (ValueError, TypeError):
                enriched_player['threat_float'] = 0.0
        
        # Add selected_by_percent as float
        if 'selected_by_percent' in enriched_player:
            try:
                enriched_player['selected_by_percent_float'] = float(enriched_player['selected_by_percent'])
            except (ValueError, TypeError):
                enriched_player['selected_by_percent_float'] = 0.0
        
        return enriched_player
    
    def _enrich_team_data(self, team: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich individual team data.
        
        Args:
            team: Team data
            
        Returns:
            Enriched team data
        """
        enriched_team = team.copy()
        
        # Add team code as string for consistency
        if 'code' in enriched_team:
            enriched_team['code_str'] = str(enriched_team['code'])
        
        return enriched_team
    
    async def _enrich_understat_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich Understat data.
        
        Args:
            data: Understat data
            
        Returns:
            Enriched Understat data
        """
        # Placeholder for Understat data enrichment
        # Will be implemented when Understat scraper is added
        return data
    
    async def _enrich_fbref_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich FBRef data.
        
        Args:
            data: FBRef data
            
        Returns:
            Enriched FBRef data
        """
        # Placeholder for FBRef data enrichment
        # Will be implemented when FBRef scraper is added
        return data
    
    async def _enrich_generic_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generic data enrichment for unknown sources.
        
        Args:
            data: Generic data
            
        Returns:
            Enriched data
        """
        # Basic enrichment for unknown sources
        enriched_data = data.copy()
        
        # Add processing metadata
        enriched_data['enriched_at'] = datetime.utcnow().isoformat()
        enriched_data['enrichment_version'] = '1.0'
        
        return enriched_data
    
    async def _add_common_enrichment(self, data: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Add common enrichment to all data sources.
        
        Args:
            data: Data to enrich
            source: Source identifier
            
        Returns:
            Data with common enrichment
        """
        enriched_data = data.copy()
        
        # Add processing metadata
        enriched_data['processed_at'] = datetime.utcnow().isoformat()
        enriched_data['processing_version'] = '1.0'
        enriched_data['data_source'] = source
        
        # Add data quality indicators
        if isinstance(data, dict):
            enriched_data['record_count'] = len(data)
            
            # Count non-null values
            non_null_count = sum(1 for value in data.values() if value is not None)
            enriched_data['completeness_score'] = non_null_count / len(data) if len(data) > 0 else 0.0
        
        return enriched_data 