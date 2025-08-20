"""
Form Consistency Features

This module contains features related to player form and consistency.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List

from ..base.feature_base import PlayerFeature
from utils.logger import get_logger

logger = get_logger("form_features")


class FormConsistencyFeature(PlayerFeature):
    """Calculate form consistency metrics"""
    
    description = "Player form consistency based on recent performance with volatility adjustment"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.lookback_gameweeks = config.get('lookback_gameweeks', 6)
        self.weights = config.get('weights', [0.3, 0.25, 0.2, 0.15, 0.08, 0.02])
        self.volatility_threshold = config.get('volatility_threshold', 1.0)
        self.ceiling_threshold = config.get('ceiling_threshold', 8.0)
    
    def calculate(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        """Calculate form consistency score for all players"""
        players_df = self.get_player_data(data)
        
        if players_df.empty:
            return pd.Series(dtype=float)
        
        # Calculate form scores for each player
        form_scores = []
        
        for _, player in players_df.iterrows():
            player_id = player.get('id')
            if not player_id:
                continue
            
            # Get player's recent performance data
            recent_scores = self._get_recent_performance(player, data)
            
            if len(recent_scores) == 0:
                # No recent data, use current form
                form_score = player.get('form', 0.0)
            else:
                # Calculate weighted average
                weighted_average = self._calculate_weighted_average(recent_scores)
                
                # Calculate volatility
                volatility = self._calculate_volatility(recent_scores)
                
                # Apply volatility penalty
                volatility_penalty = self._calculate_volatility_penalty(volatility)
                
                # Calculate ceiling bonus
                ceiling_bonus = self._calculate_ceiling_bonus(recent_scores)
                
                # Final form score
                form_score = weighted_average - volatility_penalty + ceiling_bonus
            
            form_scores.append({
                'player_id': player_id,
                'form_score': max(0.0, min(10.0, form_score))  # Clamp to 0-10
            })
        
        # Create series
        form_df = pd.DataFrame(form_scores)
        if form_df.empty:
            return pd.Series(dtype=float)
        
        return pd.Series(
            form_df['form_score'].values,
            index=form_df['player_id'].values,
            name='form_consistency'
        )
    
    def _get_recent_performance(self, player: pd.Series, data: Dict[str, pd.DataFrame]) -> List[float]:
        """Get player's recent performance scores"""
        # For now, use the player's current form and points per game
        # In a full implementation, this would use actual gameweek history
        
        form = player.get('form', 0.0)
        points_per_game = player.get('points_per_game', 0.0)
        total_points = player.get('total_points', 0.0)
        played = player.get('played', 1)
        
        # Create synthetic recent scores based on current stats
        # This is a simplified approach - in production, use actual gameweek data
        if played > 0:
            # Use points per game as base, adjusted by form
            base_score = points_per_game
            form_adjustment = (form - 5.0) * 0.5  # Adjust based on form
            recent_score = max(0.0, base_score + form_adjustment)
            
            # Create a list of recent scores (simplified)
            recent_scores = [recent_score] * min(self.lookback_gameweeks, played)
            
            # Add some variation based on form
            if form > 7.0:
                recent_scores[0] = recent_score * 1.2  # Recent boost
            elif form < 3.0:
                recent_scores[0] = recent_score * 0.8  # Recent decline
            
            return recent_scores[:self.lookback_gameweeks]
        
        return []
    
    def _calculate_weighted_average(self, scores: List[float]) -> float:
        """Calculate exponential weighted average of recent scores"""
        if not scores:
            return 0.0
        
        # Use provided weights or default exponential weights
        weights = self.weights[:len(scores)]
        
        # Normalize weights
        total_weight = sum(weights)
        if total_weight == 0:
            return 0.0
        
        normalized_weights = [w / total_weight for w in weights]
        
        # Calculate weighted average
        weighted_sum = sum(score * weight for score, weight in zip(scores, normalized_weights))
        
        return weighted_sum
    
    def _calculate_volatility(self, scores: List[float]) -> float:
        """Calculate volatility of recent scores"""
        if len(scores) < 2:
            return 0.0
        
        # Calculate standard deviation
        mean_score = np.mean(scores)
        variance = np.mean([(score - mean_score) ** 2 for score in scores])
        volatility = np.sqrt(variance)
        
        return volatility
    
    def _calculate_volatility_penalty(self, volatility: float) -> float:
        """Calculate penalty for inconsistent performance"""
        if volatility < self.volatility_threshold:
            return 0.0  # Very consistent
        elif volatility < 2.0:
            return 0.5  # Moderately consistent
        elif volatility < 3.0:
            return 1.0  # Inconsistent
        else:
            return 2.0  # Very inconsistent
    
    def _calculate_ceiling_bonus(self, scores: List[float]) -> float:
        """Calculate bonus for high ceiling performance"""
        if not scores:
            return 0.0
        
        # Check if player has shown high ceiling
        max_score = max(scores)
        if max_score >= self.ceiling_threshold:
            # Bonus for showing high ceiling
            return 0.5
        
        return 0.0
    
    def validate(self, feature_values: pd.Series) -> bool:
        """Validate form consistency feature values"""
        if feature_values.empty:
            return False
        
        # Check for reasonable bounds (0-10 scale)
        if (feature_values < 0).any() or (feature_values > 10).any():
            return False
        
        return True


class RecentFormFeature(PlayerFeature):
    """Calculate recent form based on last few gameweeks"""
    
    description = "Player recent form based on last 3 gameweeks"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.recent_gameweeks = config.get('recent_gameweeks', 3)
    
    def calculate(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        """Calculate recent form for all players"""
        players_df = self.get_player_data(data)
        
        if players_df.empty:
            return pd.Series(dtype=float)
        
        # Use current form as proxy for recent form
        # In production, this would use actual gameweek data
        recent_form_scores = []
        
        for _, player in players_df.iterrows():
            player_id = player.get('id')
            if not player_id:
                continue
            
            # Use current form, adjusted by recent performance indicators
            current_form = player.get('form', 0.0)
            points_per_game = player.get('points_per_game', 0.0)
            
            # Calculate recent form score
            recent_form = (current_form * 0.7) + (points_per_game * 0.3)
            
            recent_form_scores.append({
                'player_id': player_id,
                'recent_form': max(0.0, min(10.0, recent_form))
            })
        
        # Create series
        form_df = pd.DataFrame(recent_form_scores)
        if form_df.empty:
            return pd.Series(dtype=float)
        
        return pd.Series(
            form_df['recent_form'].values,
            index=form_df['player_id'].values,
            name='recent_form'
        )
    
    def validate(self, feature_values: pd.Series) -> bool:
        """Validate recent form feature values"""
        if feature_values.empty:
            return False
        
        # Check for reasonable bounds (0-10 scale)
        if (feature_values < 0).any() or (feature_values > 10).any():
            return False
        
        return True


class FormTrendFeature(PlayerFeature):
    """Calculate form trend (improving/declining)"""
    
    description = "Player form trend indicating if performance is improving or declining"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.trend_periods = config.get('trend_periods', 4)
    
    def calculate(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        """Calculate form trend for all players"""
        players_df = self.get_player_data(data)
        
        if players_df.empty:
            return pd.Series(dtype=float)
        
        trend_scores = []
        
        for _, player in players_df.iterrows():
            player_id = player.get('id')
            if not player_id:
                continue
            
            # Calculate trend based on form and recent performance
            current_form = player.get('form', 0.0)
            points_per_game = player.get('points_per_game', 0.0)
            total_points = player.get('total_points', 0.0)
            played = player.get('played', 1)
            
            if played < 2:
                # Not enough data for trend
                trend_score = 5.0  # Neutral
            else:
                # Simple trend calculation
                # Higher form and points per game indicate positive trend
                trend_score = (current_form * 0.6) + (points_per_game * 0.4)
                
                # Adjust based on total points vs expected
                expected_points = points_per_game * played
                if total_points > expected_points * 1.1:
                    trend_score += 0.5  # Exceeding expectations
                elif total_points < expected_points * 0.9:
                    trend_score -= 0.5  # Below expectations
            
            trend_scores.append({
                'player_id': player_id,
                'trend_score': max(0.0, min(10.0, trend_score))
            })
        
        # Create series
        trend_df = pd.DataFrame(trend_scores)
        if trend_df.empty:
            return pd.Series(dtype=float)
        
        return pd.Series(
            trend_df['trend_score'].values,
            index=trend_df['player_id'].values,
            name='form_trend'
        )
    
    def validate(self, feature_values: pd.Series) -> bool:
        """Validate form trend feature values"""
        if feature_values.empty:
            return False
        
        # Check for reasonable bounds (0-10 scale)
        if (feature_values < 0).any() or (feature_values > 10).any():
            return False
        
        return True 