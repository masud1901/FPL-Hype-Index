"""
Quality Features

This module contains features related to player quality and performance metrics.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any

from ..base.feature_base import PlayerFeature
from utils.logger import get_logger

logger = get_logger("quality_features")


class QualityFeature(PlayerFeature):
    """Calculate player quality metrics"""
    
    description = "Player quality based on performance statistics and advanced metrics"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.position_weights = config.get('position_weights', {})
    
    def calculate(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        """Calculate quality score for all players"""
        players_df = self.get_player_data(data)
        
        if players_df.empty:
            return pd.Series(dtype=float)
        
        quality_scores = []
        
        for _, player in players_df.iterrows():
            player_id = player.get('id')
            if not player_id:
                continue
            
            # Calculate position-specific quality score
            position = player.get('position', 'MID')
            quality_score = self._calculate_position_quality(player, position)
            
            quality_scores.append({
                'player_id': player_id,
                'quality_score': max(0.0, min(10.0, quality_score))
            })
        
        # Create series
        quality_df = pd.DataFrame(quality_scores)
        if quality_df.empty:
            return pd.Series(dtype=float)
        
        return pd.Series(
            quality_df['quality_score'].values,
            index=quality_df['player_id'].values,
            name='quality_score'
        )
    
    def _calculate_position_quality(self, player: pd.Series, position: str) -> float:
        """Calculate quality score based on position"""
        if position == 'GK':
            return self._calculate_goalkeeper_quality(player)
        elif position == 'DEF':
            return self._calculate_defender_quality(player)
        elif position == 'MID':
            return self._calculate_midfielder_quality(player)
        elif position == 'FWD':
            return self._calculate_forward_quality(player)
        else:
            return self._calculate_midfielder_quality(player)  # Default
    
    def _calculate_goalkeeper_quality(self, player: pd.Series) -> float:
        """Calculate goalkeeper quality score"""
        # Save performance (40%)
        saves = player.get('saves', 0)
        saves_score = min(10.0, saves / 10.0)  # Normalize saves
        
        # Clean sheet potential (30%)
        clean_sheets = player.get('clean_sheets', 0)
        clean_sheet_score = min(10.0, clean_sheets * 2.0)  # 2 points per clean sheet
        
        # Distribution quality (20%)
        # Use influence as proxy for distribution
        influence = player.get('influence', 0)
        distribution_score = min(10.0, influence / 100.0)
        
        # Bonus point potential (10%)
        bonus = player.get('bonus', 0)
        bonus_score = min(10.0, bonus * 2.0)  # 2 points per bonus
        
        # Weighted quality score
        quality_score = (
            saves_score * 0.4 +
            clean_sheet_score * 0.3 +
            distribution_score * 0.2 +
            bonus_score * 0.1
        )
        
        return quality_score
    
    def _calculate_defender_quality(self, player: pd.Series) -> float:
        """Calculate defender quality score"""
        # Clean sheet potential (40%)
        clean_sheets = player.get('clean_sheets', 0)
        clean_sheet_score = min(10.0, clean_sheets * 2.0)
        
        # Attacking returns (30%)
        goals = player.get('goals_scored', 0)
        assists = player.get('assists', 0)
        attacking_score = min(10.0, (goals * 3.0) + (assists * 2.0))
        
        # Defensive actions (20%)
        # Use influence as proxy for defensive contribution
        influence = player.get('influence', 0)
        defensive_score = min(10.0, influence / 100.0)
        
        # Bonus point potential (10%)
        bonus = player.get('bonus', 0)
        bonus_score = min(10.0, bonus * 2.0)
        
        # Weighted quality score
        quality_score = (
            clean_sheet_score * 0.4 +
            attacking_score * 0.3 +
            defensive_score * 0.2 +
            bonus_score * 0.1
        )
        
        return quality_score
    
    def _calculate_midfielder_quality(self, player: pd.Series) -> float:
        """Calculate midfielder quality score"""
        # Goal threat (30%)
        goals = player.get('goals_scored', 0)
        goal_threat = min(10.0, goals * 3.0)
        
        # Creativity (30%)
        assists = player.get('assists', 0)
        creativity = player.get('creativity', 0)
        creativity_score = min(10.0, (assists * 2.0) + (creativity / 100.0))
        
        # Defensive contribution (20%)
        influence = player.get('influence', 0)
        defensive_score = min(10.0, influence / 100.0)
        
        # Bonus point potential (20%)
        bonus = player.get('bonus', 0)
        bonus_score = min(10.0, bonus * 2.0)
        
        # Weighted quality score
        quality_score = (
            goal_threat * 0.3 +
            creativity_score * 0.3 +
            defensive_score * 0.2 +
            bonus_score * 0.2
        )
        
        return quality_score
    
    def _calculate_forward_quality(self, player: pd.Series) -> float:
        """Calculate forward quality score"""
        # Finishing (40%)
        goals = player.get('goals_scored', 0)
        finishing_score = min(10.0, goals * 2.5)
        
        # Goal threat (30%)
        threat = player.get('threat', 0)
        goal_threat = min(10.0, threat / 100.0)
        
        # Assist potential (20%)
        assists = player.get('assists', 0)
        assist_score = min(10.0, assists * 2.0)
        
        # Bonus point potential (10%)
        bonus = player.get('bonus', 0)
        bonus_score = min(10.0, bonus * 2.0)
        
        # Weighted quality score
        quality_score = (
            finishing_score * 0.4 +
            goal_threat * 0.3 +
            assist_score * 0.2 +
            bonus_score * 0.1
        )
        
        return quality_score
    
    def validate(self, feature_values: pd.Series) -> bool:
        """Validate quality feature values"""
        if feature_values.empty:
            return False
        
        # Check for reasonable bounds (0-10 scale)
        if (feature_values < 0).any() or (feature_values > 10).any():
            return False
        
        return True


class PerformanceQualityFeature(PlayerFeature):
    """Calculate performance-based quality metrics"""
    
    description = "Player quality based on performance efficiency and consistency"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.efficiency_threshold = config.get('efficiency_threshold', 20.0)
    
    def calculate(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        """Calculate performance quality for all players"""
        players_df = self.get_player_data(data)
        
        if players_df.empty:
            return pd.Series(dtype=float)
        
        performance_scores = []
        
        for _, player in players_df.iterrows():
            player_id = player.get('id')
            if not player_id:
                continue
            
            # Calculate performance quality score
            performance_score = self._calculate_performance_quality(player)
            
            performance_scores.append({
                'player_id': player_id,
                'performance_score': max(0.0, min(10.0, performance_score))
            })
        
        # Create series
        performance_df = pd.DataFrame(performance_scores)
        if performance_df.empty:
            return pd.Series(dtype=float)
        
        return pd.Series(
            performance_df['performance_score'].values,
            index=performance_df['player_id'].values,
            name='performance_quality'
        )
    
    def _calculate_performance_quality(self, player: pd.Series) -> float:
        """Calculate performance quality score"""
        # Points per game efficiency (40%)
        points_per_game = player.get('points_per_game', 0.0)
        efficiency_score = min(10.0, points_per_game / 2.0)  # 2 points per game = 10 score
        
        # ICT Index (30%)
        ict_index = player.get('ict_index', 0.0)
        ict_score = min(10.0, ict_index / 200.0)  # 200 ICT = 10 score
        
        # Bonus point efficiency (20%)
        bonus = player.get('bonus', 0)
        played = max(player.get('played', 1), 1)
        bonus_per_game = bonus / played
        bonus_score = min(10.0, bonus_per_game * 5.0)  # 2 bonus per game = 10 score
        
        # Consistency (10%)
        form = player.get('form', 0.0)
        consistency_score = min(10.0, form / 10.0)
        
        # Weighted performance score
        performance_score = (
            efficiency_score * 0.4 +
            ict_score * 0.3 +
            bonus_score * 0.2 +
            consistency_score * 0.1
        )
        
        return performance_score
    
    def validate(self, feature_values: pd.Series) -> bool:
        """Validate performance quality feature values"""
        if feature_values.empty:
            return False
        
        # Check for reasonable bounds (0-10 scale)
        if (feature_values < 0).any() or (feature_values > 10).any():
            return False
        
        return True 