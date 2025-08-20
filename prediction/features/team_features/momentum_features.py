"""
Team Momentum Features

This module contains features related to team momentum and form.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List

from ..base.feature_base import TeamFeature
from utils.logger import get_logger

logger = get_logger("momentum_features")


class TeamMomentumFeature(TeamFeature):
    """Calculate team momentum metrics"""
    
    description = "Team momentum based on recent results and performance trends"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.recent_results_weight = config.get('recent_results_weight', 0.4)
        self.goal_difference_weight = config.get('goal_difference_weight', 0.3)
        self.expected_performance_weight = config.get('expected_performance_weight', 0.3)
        self.lookback_gameweeks = config.get('lookback_gameweeks', 5)
    
    def calculate(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        """Calculate momentum score for all teams"""
        teams_df = self.get_team_data(data)
        
        if teams_df.empty:
            return pd.Series(dtype=float)
        
        momentum_scores = []
        
        for _, team in teams_df.iterrows():
            team_name = team.get('name')
            if not team_name:
                continue
            
            # Calculate momentum score
            momentum_score = self._calculate_team_momentum(team)
            
            momentum_scores.append({
                'team_name': team_name,
                'momentum_score': max(0.0, min(10.0, momentum_score))
            })
        
        # Create series
        momentum_df = pd.DataFrame(momentum_scores)
        if momentum_df.empty:
            return pd.Series(dtype=float)
        
        return pd.Series(
            momentum_df['momentum_score'].values,
            index=momentum_df['team_name'].values,
            name='team_momentum'
        )
    
    def _calculate_team_momentum(self, team: pd.Series) -> float:
        """Calculate momentum score for a team"""
        # Recent results component (40%)
        recent_results = self._calculate_recent_results_score(team)
        
        # Goal difference component (30%)
        goal_difference = self._calculate_goal_difference_score(team)
        
        # Expected performance component (30%)
        expected_performance = self._calculate_expected_performance_score(team)
        
        # Weighted momentum score
        momentum_score = (
            recent_results * self.recent_results_weight +
            goal_difference * self.goal_difference_weight +
            expected_performance * self.expected_performance_weight
        )
        
        return momentum_score
    
    def _calculate_recent_results_score(self, team: pd.Series) -> float:
        """Calculate recent results score"""
        # Use team form as proxy for recent results
        form = team.get('form', 50.0)
        
        # Convert form to 0-10 scale
        form_score = form / 10.0
        
        # Add bonus for recent wins
        wins = team.get('win', 0)
        draws = team.get('draw', 0)
        played = max(team.get('played', 1), 1)
        
        win_rate = wins / played
        draw_rate = draws / played
        
        # Recent results score
        results_score = (win_rate * 3.0) + (draw_rate * 1.0)  # 3 points for win, 1 for draw
        
        # Combine form and results
        recent_score = (form_score * 0.7) + (results_score * 0.3)
        
        return min(10.0, recent_score * 10.0)
    
    def _calculate_goal_difference_score(self, team: pd.Series) -> float:
        """Calculate goal difference score"""
        goals_for = team.get('goals_for', 0)
        goals_against = team.get('goals_against', 0)
        played = max(team.get('played', 1), 1)
        
        # Calculate goal difference per game
        goal_diff_per_game = (goals_for - goals_against) / played
        
        # Convert to 0-10 scale
        # Positive goal difference = good, negative = bad
        if goal_diff_per_game >= 1.0:
            gd_score = 10.0
        elif goal_diff_per_game >= 0.5:
            gd_score = 8.0
        elif goal_diff_per_game >= 0.0:
            gd_score = 6.0
        elif goal_diff_per_game >= -0.5:
            gd_score = 4.0
        elif goal_diff_per_game >= -1.0:
            gd_score = 2.0
        else:
            gd_score = 0.0
        
        return gd_score
    
    def _calculate_expected_performance_score(self, team: pd.Series) -> float:
        """Calculate expected performance score"""
        # Use team strength and position as proxy for expected performance
        strength = team.get('strength', 50.0)
        position = team.get('position', 10)
        
        # Strength score (0-10 scale)
        strength_score = strength / 10.0
        
        # Position score (lower position = better team)
        position_score = max(0.0, (20 - position) / 20.0) * 10.0
        
        # Expected performance score
        expected_score = (strength_score * 0.6) + (position_score * 0.4)
        
        return expected_score
    
    def validate(self, feature_values: pd.Series) -> bool:
        """Validate momentum feature values"""
        if feature_values.empty:
            return False
        
        # Check for reasonable bounds (0-10 scale)
        if (feature_values < 0).any() or (feature_values > 10).any():
            return False
        
        return True


class TeamFormFeature(TeamFeature):
    """Calculate team form metrics"""
    
    description = "Team form based on recent performance and consistency"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.form_periods = config.get('form_periods', 6)
    
    def calculate(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        """Calculate form score for all teams"""
        teams_df = self.get_team_data(data)
        
        if teams_df.empty:
            return pd.Series(dtype=float)
        
        form_scores = []
        
        for _, team in teams_df.iterrows():
            team_name = team.get('name')
            if not team_name:
                continue
            
            # Calculate form score
            form_score = self._calculate_team_form(team)
            
            form_scores.append({
                'team_name': team_name,
                'form_score': max(0.0, min(10.0, form_score))
            })
        
        # Create series
        form_df = pd.DataFrame(form_scores)
        if form_df.empty:
            return pd.Series(dtype=float)
        
        return pd.Series(
            form_df['form_score'].values,
            index=form_df['team_name'].values,
            name='team_form'
        )
    
    def _calculate_team_form(self, team: pd.Series) -> float:
        """Calculate form score for a team"""
        # Use team form directly
        form = team.get('form', 50.0)
        
        # Convert to 0-10 scale
        form_score = form / 10.0
        
        # Add consistency bonus
        consistency_bonus = self._calculate_consistency_bonus(team)
        
        # Final form score
        final_form = form_score + consistency_bonus
        
        return min(10.0, final_form)
    
    def _calculate_consistency_bonus(self, team: pd.Series) -> float:
        """Calculate consistency bonus for team"""
        wins = team.get('win', 0)
        draws = team.get('draw', 0)
        losses = team.get('loss', 0)
        played = max(team.get('played', 1), 1)
        
        # Calculate consistency based on win/draw/loss distribution
        win_rate = wins / played
        draw_rate = draws / played
        loss_rate = losses / played
        
        # Consistency bonus (teams with balanced results get bonus)
        if win_rate > 0.6 or loss_rate > 0.6:
            # Very consistent (good or bad)
            consistency_bonus = 0.5
        elif win_rate > 0.4 or loss_rate > 0.4:
            # Moderately consistent
            consistency_bonus = 0.3
        else:
            # Inconsistent
            consistency_bonus = 0.0
        
        return consistency_bonus
    
    def validate(self, feature_values: pd.Series) -> bool:
        """Validate form feature values"""
        if feature_values.empty:
            return False
        
        # Check for reasonable bounds (0-10 scale)
        if (feature_values < 0).any() or (feature_values > 10).any():
            return False
        
        return True


class TeamStrengthFeature(TeamFeature):
    """Calculate team strength metrics"""
    
    description = "Team strength based on overall performance and squad quality"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.strength_weights = config.get('strength_weights', {
            'position': 0.3,
            'points': 0.3,
            'goal_difference': 0.2,
            'squad_quality': 0.2
        })
    
    def calculate(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        """Calculate strength score for all teams"""
        teams_df = self.get_team_data(data)
        
        if teams_df.empty:
            return pd.Series(dtype=float)
        
        strength_scores = []
        
        for _, team in teams_df.iterrows():
            team_name = team.get('name')
            if not team_name:
                continue
            
            # Calculate strength score
            strength_score = self._calculate_team_strength(team)
            
            strength_scores.append({
                'team_name': team_name,
                'strength_score': max(0.0, min(10.0, strength_score))
            })
        
        # Create series
        strength_df = pd.DataFrame(strength_scores)
        if strength_df.empty:
            return pd.Series(dtype=float)
        
        return pd.Series(
            strength_df['strength_score'].values,
            index=strength_df['team_name'].values,
            name='team_strength'
        )
    
    def _calculate_team_strength(self, team: pd.Series) -> float:
        """Calculate strength score for a team"""
        # Position component (30%)
        position = team.get('position', 10)
        position_score = max(0.0, (20 - position) / 20.0) * 10.0
        
        # Points component (30%)
        points = team.get('points', 0)
        played = max(team.get('played', 1), 1)
        points_per_game = points / played
        points_score = min(10.0, points_per_game / 3.0 * 10.0)  # 3 points per game = 10 score
        
        # Goal difference component (20%)
        goals_for = team.get('goals_for', 0)
        goals_against = team.get('goals_against', 0)
        goal_diff_per_game = (goals_for - goals_against) / played
        gd_score = max(0.0, min(10.0, (goal_diff_per_game + 1.0) * 5.0))  # -1 to +1 range
        
        # Squad quality component (20%)
        squad_quality = self._calculate_squad_quality(team)
        
        # Weighted strength score
        strength_score = (
            position_score * self.strength_weights['position'] +
            points_score * self.strength_weights['points'] +
            gd_score * self.strength_weights['goal_difference'] +
            squad_quality * self.strength_weights['squad_quality']
        )
        
        return strength_score
    
    def _calculate_squad_quality(self, team: pd.Series) -> float:
        """Calculate squad quality score"""
        # Use average player points as proxy for squad quality
        avg_player_points = team.get('avg_player_points', 0.0)
        
        # Convert to 0-10 scale
        squad_quality = min(10.0, avg_player_points / 100.0 * 10.0)
        
        return squad_quality
    
    def validate(self, feature_values: pd.Series) -> bool:
        """Validate strength feature values"""
        if feature_values.empty:
            return False
        
        # Check for reasonable bounds (0-10 scale)
        if (feature_values < 0).any() or (feature_values > 10).any():
            return False
        
        return True 