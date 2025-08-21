"""
Data Integration Service

This service manages the complete data flow:
1. Fetch data from PostgreSQL
2. Run predictions using the prediction engine
3. Cache results in Redis (1 day TTL)
4. Serve cached results via API
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from storage.database import DatabaseManager
from utils.cache import get_cache, cache_player_score, get_cached_player_score
from prediction.scoring.master_score.player_impact_score import PlayerImpactScore
from prediction.optimization.algorithms.transfer_optimizer import TransferOptimizer
from config.settings import get_settings

logger = logging.getLogger(__name__)


class DataIntegrationService:
    """Manages data flow between PostgreSQL, Prediction Engine, and Redis."""
    
    def __init__(self):
        """Initialize the data integration service."""
        self.settings = get_settings()
        self.db_manager = DatabaseManager(self.settings.database_url)
        self.cache = get_cache()
        self.scorer = PlayerImpactScore(self.settings.dict())
        self.optimizer = TransferOptimizer(self.settings.dict())
        
    async def initialize(self):
        """Initialize database connection and create tables."""
        await self.db_manager.connect()
        await self.db_manager.create_tables()
        logger.info("Data integration service initialized")
    
    async def close(self):
        """Close database connection."""
        await self.db_manager.disconnect()
        logger.info("Data integration service closed")
    
    async def get_player_scores(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get player scores with caching.
        
        Args:
            force_refresh: Force refresh from database and prediction engine
            
        Returns:
            List of player scores with PIS calculations
        """
        cache_key = "player_scores_all"
        
        # Check cache first (unless force refresh)
        if not force_refresh:
            cached_scores = self.cache.get(cache_key)
            if cached_scores:
                logger.info(f"Retrieved {len(cached_scores)} player scores from cache")
                return cached_scores
        
        # Fetch from database and calculate scores
        logger.info("Fetching player data from database and calculating scores...")
        players = await self.db_manager.get_all_players()
        
        if not players:
            logger.warning("No players found in database")
            return []
        
        # Calculate PIS for each player
        scored_players = []
        for player in players:
            try:
                score_result = self.scorer.calculate_pis(player)
                scored_player = {
                    **player,
                    'pis_score': score_result['final_pis'],
                    'confidence': score_result['confidence'],
                    'sub_scores': score_result['sub_scores'],
                    'calculated_at': datetime.now().isoformat()
                }
                scored_players.append(scored_player)
                
                # Cache individual player score
                cache_player_score(str(player['id']), scored_player)
                
            except Exception as e:
                logger.error(f"Failed to calculate score for player {player.get('name', 'Unknown')}: {e}")
                continue
        
        # Cache all scores (1 day TTL)
        self.cache.set(cache_key, scored_players, ttl=86400)  # 24 hours
        logger.info(f"Calculated and cached {len(scored_players)} player scores")
        
        return scored_players
    
    async def get_player_score(self, player_id: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get score for a specific player.
        
        Args:
            player_id: Player ID
            force_refresh: Force refresh from database
            
        Returns:
            Player score data or None
        """
        # Check cache first
        if not force_refresh:
            cached_score = get_cached_player_score(player_id)
            if cached_score:
                return cached_score
        
        # Fetch from database and calculate
        players = await self.db_manager.get_all_players()
        player = next((p for p in players if str(p['id']) == player_id), None)
        
        if not player:
            return None
        
        try:
            score_result = self.scorer.calculate_pis(player)
            scored_player = {
                **player,
                'pis_score': score_result['final_pis'],
                'confidence': score_result['confidence'],
                'sub_scores': score_result['sub_scores'],
                'calculated_at': datetime.now().isoformat()
            }
            
            # Cache the result
            cache_player_score(player_id, scored_player)
            return scored_player
            
        except Exception as e:
            logger.error(f"Failed to calculate score for player {player.get('name', 'Unknown')}: {e}")
            return None
    
    async def get_transfer_recommendations(
        self, 
        current_squad: List[Dict[str, Any]], 
        budget: float = 2.0,
        strategy: str = "balanced",
        force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get transfer recommendations with caching.
        
        Args:
            current_squad: Current squad players
            budget: Available budget
            strategy: Transfer strategy
            force_refresh: Force refresh from prediction engine
            
        Returns:
            List of transfer recommendations
        """
        # Generate cache key based on squad and parameters
        squad_hash = str(hash(tuple(sorted([p['id'] for p in current_squad]))))
        cache_key = f"transfer_recommendations:{squad_hash}:{strategy}:{budget}"
        
        # Check cache first
        if not force_refresh:
            cached_recommendations = self.cache.get(cache_key)
            if cached_recommendations:
                logger.info(f"Retrieved {len(cached_recommendations)} transfer recommendations from cache")
                return cached_recommendations
        
        # Get available players from database
        all_players = await self.db_manager.get_all_players()
        
        # Filter out players already in squad
        squad_player_ids = {p['id'] for p in current_squad}
        available_players = [p for p in all_players if p['id'] not in squad_player_ids]
        
        if not available_players:
            logger.warning("No available players found for transfers")
            return []
        
        # Get transfer recommendations
        try:
            recommendations = self.optimizer.get_single_transfer_recommendations(
                current_squad=current_squad,
                available_players=available_players,
                budget=budget
            )
            
            # Convert to serializable format
            serializable_recommendations = []
            for rec in recommendations:
                serializable_rec = {
                    'player_out': {
                        'id': rec.player_out['id'],
                        'name': rec.player_out['name'],
                        'team': rec.player_out['team'],
                        'position': rec.player_out['position'],
                        'price': rec.player_out['price']
                    },
                    'player_in': {
                        'id': rec.player_in['id'],
                        'name': rec.player_in['name'],
                        'team': rec.player_in['team'],
                        'position': rec.player_in['position'],
                        'price': rec.player_in['price']
                    },
                    'expected_points_gain': rec.expected_points_gain,
                    'confidence_score': rec.confidence_score,
                    'risk_score': rec.risk_score,
                    'reasoning': rec.reasoning,
                    'calculated_at': datetime.now().isoformat()
                }
                serializable_recommendations.append(serializable_rec)
            
            # Cache recommendations (1 day TTL)
            self.cache.set(cache_key, serializable_recommendations, ttl=86400)
            logger.info(f"Generated and cached {len(serializable_recommendations)} transfer recommendations")
            
            return serializable_recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate transfer recommendations: {e}")
            return []
    
    async def get_players_by_position(self, position: str) -> List[Dict[str, Any]]:
        """
        Get players by position with scores.
        
        Args:
            position: Player position (GK, DEF, MID, FWD)
            
        Returns:
            List of players with scores for the position
        """
        cache_key = f"players_by_position:{position}"
        
        # Check cache first
        cached_players = self.cache.get(cache_key)
        if cached_players:
            return cached_players
        
        # Fetch from database
        players = await self.db_manager.get_players_by_position(position)
        
        # Calculate scores
        scored_players = []
        for player in players:
            try:
                score_result = self.scorer.calculate_pis(player)
                scored_player = {
                    **player,
                    'pis_score': score_result['final_pis'],
                    'confidence': score_result['confidence'],
                    'sub_scores': score_result['sub_scores']
                }
                scored_players.append(scored_player)
            except Exception as e:
                logger.error(f"Failed to calculate score for {player.get('name', 'Unknown')}: {e}")
                continue
        
        # Cache results (1 day TTL)
        self.cache.set(cache_key, scored_players, ttl=86400)
        
        return scored_players
    
    async def refresh_all_cache(self):
        """Refresh all cached data."""
        logger.info("Refreshing all cached data...")
        
        # Refresh player scores
        await self.get_player_scores(force_refresh=True)
        
        # Refresh position-based player lists
        positions = ['GK', 'DEF', 'MID', 'FWD']
        for position in positions:
            await self.get_players_by_position(position)
        
        logger.info("All cache refreshed successfully")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = self.cache.get_stats()
        
        # Add custom stats
        stats['cache_keys'] = {
            'player_scores_all': self.cache.exists('player_scores_all'),
            'players_by_position_gk': self.cache.exists('players_by_position:GK'),
            'players_by_position_def': self.cache.exists('players_by_position:DEF'),
            'players_by_position_mid': self.cache.exists('players_by_position:MID'),
            'players_by_position_fwd': self.cache.exists('players_by_position:FWD'),
        }
        
        return stats
    
    async def clear_cache(self):
        """Clear all cached data."""
        logger.info("Clearing all cached data...")
        
        # Clear all FPL-related cache
        keys = self.cache.redis_client.keys('fpl:*')
        if keys:
            self.cache.redis_client.delete(*keys)
            logger.info(f"Cleared {len(keys)} cache entries")
        else:
            logger.info("No cache entries to clear")


# Global service instance
_data_integration_service: Optional[DataIntegrationService] = None


async def get_data_integration_service() -> DataIntegrationService:
    """Get the global data integration service instance."""
    global _data_integration_service
    
    if _data_integration_service is None:
        _data_integration_service = DataIntegrationService()
        await _data_integration_service.initialize()
    
    return _data_integration_service


async def close_data_integration_service():
    """Close the global data integration service."""
    global _data_integration_service
    
    if _data_integration_service:
        await _data_integration_service.close()
        _data_integration_service = None 