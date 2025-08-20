"""
Value Features

This module contains features related to player value and cost efficiency.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any

from ..base.feature_base import PlayerFeature
from utils.logger import get_logger

logger = get_logger("value_features")


class ValueFeature(PlayerFeature):
    """Calculate player value metrics"""
    
    description = "Player value based on cost efficiency and points per million"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.points_per_million_threshold = config.get('points_per_million_threshold', 20.0)
        self.price_efficiency_weight = config.get('price_efficiency_weight', 0.7)
        self.ownership_penalty = config.get('ownership_penalty', 0.1)
    
    def calculate(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        """Calculate value score for all players"""
        players_df = self.get_player_data(data)
        
        if players_df.empty:
            return pd.Series(dtype=float)
        
        value_scores = []
        
        for _, player in players_df.iterrows():
            player_id = player.get('id')
            if not player_id:
                continue
            
            # Calculate value score
            value_score = self._calculate_value_score(player)
            
            value_scores.append({
                'player_id': player_id,
                'value_score': max(0.0, min(10.0, value_score))
            })
        
        # Create series
        value_df = pd.DataFrame(value_scores)
        if value_df.empty:
            return pd.Series(dtype=float)
        
        return pd.Series(
            value_df['value_score'].values,
            index=value_df['player_id'].values,
            name='value_score'
        )
    
    def _calculate_value_score(self, player: pd.Series) -> float:
        """Calculate value score for a player"""
        total_points = player.get('total_points', 0)
        price = player.get('price', 1.0)
        selected_by_percent = player.get('selected_by_percent', 0.0)
        
        # Calculate points per million
        if price > 0:
            points_per_million = total_points / price
        else:
            points_per_million = 0.0
        
        # Base value score (0-10 scale)
        if points_per_million >= self.points_per_million_threshold:
            base_score = 10.0
        else:
            base_score = (points_per_million / self.points_per_million_threshold) * 10.0
        
        # Price efficiency bonus (cheaper players get bonus)
        price_efficiency = max(0.0, (15.0 - price) / 15.0)  # 15.0 is max price
        price_bonus = price_efficiency * 2.0  # Up to 2 points bonus
        
        # Ownership penalty (high ownership = lower differential potential)
        ownership_penalty = (selected_by_percent / 100.0) * self.ownership_penalty
        
        # Final value score
        value_score = base_score + price_bonus - ownership_penalty
        
        return max(0.0, min(10.0, value_score))
    
    def validate(self, feature_values: pd.Series) -> bool:
        """Validate value feature values"""
        if feature_values.empty:
            return False
        
        # Check for reasonable bounds (0-10 scale)
        if (feature_values < 0).any() or (feature_values > 10).any():
            return False
        
        return True


class PointsPerMillionFeature(PlayerFeature):
    """Calculate points per million metric"""
    
    description = "Player points per million spent"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.normalization_factor = config.get('normalization_factor', 20.0)
    
    def calculate(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        """Calculate points per million for all players"""
        players_df = self.get_player_data(data)
        
        if players_df.empty:
            return pd.Series(dtype=float)
        
        ppm_scores = []
        
        for _, player in players_df.iterrows():
            player_id = player.get('id')
            if not player_id:
                continue
            
            # Calculate points per million
            total_points = player.get('total_points', 0)
            price = player.get('price', 1.0)
            
            if price > 0:
                points_per_million = total_points / price
            else:
                points_per_million = 0.0
            
            # Normalize to 0-10 scale
            normalized_score = min(10.0, points_per_million / self.normalization_factor * 10.0)
            
            ppm_scores.append({
                'player_id': player_id,
                'ppm_score': normalized_score
            })
        
        # Create series
        ppm_df = pd.DataFrame(ppm_scores)
        if ppm_df.empty:
            return pd.Series(dtype=float)
        
        return pd.Series(
            ppm_df['ppm_score'].values,
            index=ppm_df['player_id'].values,
            name='points_per_million'
        )
    
    def validate(self, feature_values: pd.Series) -> bool:
        """Validate points per million feature values"""
        if feature_values.empty:
            return False
        
        # Check for reasonable bounds (0-10 scale)
        if (feature_values < 0).any() or (feature_values > 10).any():
            return False
        
        return True


class PriceEfficiencyFeature(PlayerFeature):
    """Calculate price efficiency metrics"""
    
    description = "Player price efficiency relative to position and performance"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.position_price_weights = config.get('position_price_weights', {
            'GK': 1.0,
            'DEF': 1.2,
            'MID': 1.0,
            'FWD': 1.1
        })
    
    def calculate(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        """Calculate price efficiency for all players"""
        players_df = self.get_player_data(data)
        
        if players_df.empty:
            return pd.Series(dtype=float)
        
        efficiency_scores = []
        
        for _, player in players_df.iterrows():
            player_id = player.get('id')
            if not player_id:
                continue
            
            # Calculate price efficiency
            efficiency_score = self._calculate_price_efficiency(player)
            
            efficiency_scores.append({
                'player_id': player_id,
                'efficiency_score': max(0.0, min(10.0, efficiency_score))
            })
        
        # Create series
        efficiency_df = pd.DataFrame(efficiency_scores)
        if efficiency_df.empty:
            return pd.Series(dtype=float)
        
        return pd.Series(
            efficiency_df['efficiency_score'].values,
            index=efficiency_df['player_id'].values,
            name='price_efficiency'
        )
    
    def _calculate_price_efficiency(self, player: pd.Series) -> float:
        """Calculate price efficiency for a player"""
        position = player.get('position', 'MID')
        price = player.get('price', 1.0)
        total_points = player.get('total_points', 0)
        points_per_game = player.get('points_per_game', 0.0)
        
        # Get position-specific price weight
        position_weight = self.position_price_weights.get(position, 1.0)
        
        # Calculate expected price based on performance
        expected_price = points_per_game * position_weight * 2.0  # Rough estimate
        
        # Calculate efficiency (lower actual price relative to expected = higher efficiency)
        if expected_price > 0:
            efficiency_ratio = expected_price / price
        else:
            efficiency_ratio = 1.0
        
        # Convert to 0-10 scale
        efficiency_score = min(10.0, efficiency_ratio * 5.0)  # 2.0 ratio = 10 score
        
        return efficiency_score
    
    def validate(self, feature_values: pd.Series) -> bool:
        """Validate price efficiency feature values"""
        if feature_values.empty:
            return False
        
        # Check for reasonable bounds (0-10 scale)
        if (feature_values < 0).any() or (feature_values > 10).any():
            return False
        
        return True


class DifferentialValueFeature(PlayerFeature):
    """Calculate differential value (low ownership, high potential)"""
    
    description = "Player differential value based on low ownership and high potential"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.ownership_threshold = config.get('ownership_threshold', 10.0)
        self.potential_threshold = config.get('potential_threshold', 7.0)
    
    def calculate(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        """Calculate differential value for all players"""
        players_df = self.get_player_data(data)
        
        if players_df.empty:
            return pd.Series(dtype=float)
        
        differential_scores = []
        
        for _, player in players_df.iterrows():
            player_id = player.get('id')
            if not player_id:
                continue
            
            # Calculate differential value
            differential_score = self._calculate_differential_value(player)
            
            differential_scores.append({
                'player_id': player_id,
                'differential_score': max(0.0, min(10.0, differential_score))
            })
        
        # Create series
        differential_df = pd.DataFrame(differential_scores)
        if differential_df.empty:
            return pd.Series(dtype=float)
        
        return pd.Series(
            differential_df['differential_score'].values,
            index=differential_df['player_id'].values,
            name='differential_value'
        )
    
    def _calculate_differential_value(self, player: pd.Series) -> float:
        """Calculate differential value for a player"""
        selected_by_percent = player.get('selected_by_percent', 0.0)
        form = player.get('form', 0.0)
        points_per_game = player.get('points_per_game', 0.0)
        
        # Low ownership bonus (lower ownership = higher differential potential)
        ownership_bonus = max(0.0, (self.ownership_threshold - selected_by_percent) / self.ownership_threshold) * 5.0
        
        # High potential bonus (high form and points per game)
        potential_score = (form + points_per_game) / 2.0
        potential_bonus = max(0.0, (potential_score - self.potential_threshold) / (10.0 - self.potential_threshold)) * 5.0
        
        # Combined differential score
        differential_score = ownership_bonus + potential_bonus
        
        return differential_score
    
    def validate(self, feature_values: pd.Series) -> bool:
        """Validate differential value feature values"""
        if feature_values.empty:
            return False
        
        # Check for reasonable bounds (0-10 scale)
        if (feature_values < 0).any() or (feature_values > 10).any():
            return False
        
        return True 