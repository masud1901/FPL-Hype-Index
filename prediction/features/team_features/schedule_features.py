"""
Team Schedule Features

This module contains features related to team schedules and fixture difficulty.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List

from ..base.feature_base import TeamFeature
from utils.logger import get_logger

logger = get_logger("schedule_features")


class TeamScheduleFeature(TeamFeature):
    """Calculate team schedule difficulty and features"""
    
    description = "Team schedule difficulty based on upcoming fixtures"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.lookahead_gameweeks = config.get('lookahead_gameweeks', 5)
        self.home_advantage = config.get('home_advantage', 0.5)
        self.away_penalty = config.get('away_penalty', -0.5)
        self.difficulty_multipliers = config.get('difficulty_multipliers', {
            'very_easy': 1.2,
            'easy': 1.1,
            'medium': 1.0,
            'hard': 0.9,
            'very_hard': 0.8
        })
    
    def calculate(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        """Calculate schedule difficulty for all teams"""
        teams_df = self.get_team_data(data)
        fixtures_df = self.get_fixture_data(data)
        
        if teams_df.empty or fixtures_df.empty:
            return pd.Series(dtype=float)
        
        schedule_scores = []
        
        for _, team in teams_df.iterrows():
            team_name = team.get('name')
            if not team_name:
                continue
            
            # Get team's upcoming fixtures
            team_fixtures = self._get_team_fixtures(fixtures_df, team_name)
            
            if team_fixtures.empty:
                # No upcoming fixtures, use neutral score
                schedule_score = 5.0
            else:
                # Calculate schedule difficulty
                schedule_score = self._calculate_schedule_difficulty(team_fixtures, team)
            
            schedule_scores.append({
                'team_name': team_name,
                'schedule_score': max(0.0, min(10.0, schedule_score))
            })
        
        # Create series
        schedule_df = pd.DataFrame(schedule_scores)
        if schedule_df.empty:
            return pd.Series(dtype=float)
        
        return pd.Series(
            schedule_df['schedule_score'].values,
            index=schedule_df['team_name'].values,
            name='schedule_difficulty'
        )
    
    def _get_team_fixtures(self, fixtures_df: pd.DataFrame, team_name: str) -> pd.DataFrame:
        """Get upcoming fixtures for a specific team"""
        team_fixtures = fixtures_df[
            (fixtures_df['home_team_name'] == team_name) | 
            (fixtures_df['away_team_name'] == team_name)
        ].copy()
        
        # Add home/away indicator
        team_fixtures['home_away'] = team_fixtures.apply(
            lambda row: 'H' if row['home_team_name'] == team_name else 'A', axis=1
        )
        
        # Sort by gameweek
        team_fixtures = team_fixtures.sort_values('event')
        
        return team_fixtures.head(self.lookahead_gameweeks)
    
    def _calculate_schedule_difficulty(self, team_fixtures: pd.DataFrame, team: pd.Series) -> float:
        """Calculate overall schedule difficulty for a team"""
        if team_fixtures.empty:
            return 5.0  # Neutral difficulty
        
        fixture_difficulties = []
        
        for _, fixture in team_fixtures.iterrows():
            difficulty = self._calculate_fixture_difficulty(fixture, team)
            fixture_difficulties.append(difficulty)
        
        # Calculate weighted average (earlier fixtures weighted more)
        weights = self._get_fixture_weights(len(fixture_difficulties))
        weighted_difficulty = sum(d * w for d, w in zip(fixture_difficulties, weights))
        
        return weighted_difficulty
    
    def _calculate_fixture_difficulty(self, fixture: pd.Series, team: pd.Series) -> float:
        """Calculate difficulty for a single fixture"""
        home_away = fixture.get('home_away', 'H')
        
        # Get opponent strength
        if home_away == 'H':
            opponent_strength = fixture.get('away_team_strength', 50.0)
        else:
            opponent_strength = fixture.get('home_team_strength', 50.0)
        
        # Base difficulty (higher = easier fixture)
        base_difficulty = 10.0 - (opponent_strength / 10.0)
        
        # Apply home/away adjustment
        if home_away == 'H':
            base_difficulty += self.home_advantage
        else:
            base_difficulty += self.away_penalty
        
        # Apply team strength adjustment
        team_strength = team.get('strength', 50.0)
        strength_adjustment = (team_strength - 50.0) / 100.0
        base_difficulty += strength_adjustment
        
        return max(1.0, min(10.0, base_difficulty))
    
    def _get_fixture_weights(self, num_fixtures: int) -> List[float]:
        """Get weights for fixtures (earlier fixtures weighted more)"""
        if num_fixtures == 0:
            return []
        
        # Exponential decay weights
        weights = [0.4, 0.25, 0.2, 0.1, 0.05][:num_fixtures]
        
        # Normalize weights
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]
        
        return normalized_weights
    
    def validate(self, feature_values: pd.Series) -> bool:
        """Validate schedule difficulty feature values"""
        if feature_values.empty:
            return False
        
        # Check for reasonable bounds (0-10 scale)
        if (feature_values < 0).any() or (feature_values > 10).any():
            return False
        
        return True


class FixtureCongestionFeature(TeamFeature):
    """Calculate fixture congestion for teams"""
    
    description = "Team fixture congestion based on fixture density and rest periods"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.congestion_threshold = config.get('congestion_threshold', 3)  # fixtures per week
        self.rest_penalty = config.get('rest_penalty', 0.5)
    
    def calculate(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        """Calculate fixture congestion for all teams"""
        teams_df = self.get_team_data(data)
        fixtures_df = self.get_fixture_data(data)
        
        if teams_df.empty or fixtures_df.empty:
            return pd.Series(dtype=float)
        
        congestion_scores = []
        
        for _, team in teams_df.iterrows():
            team_name = team.get('name')
            if not team_name:
                continue
            
            # Get team's upcoming fixtures
            team_fixtures = self._get_team_fixtures(fixtures_df, team_name)
            
            if team_fixtures.empty:
                # No upcoming fixtures, use neutral score
                congestion_score = 5.0
            else:
                # Calculate congestion score
                congestion_score = self._calculate_congestion_score(team_fixtures)
            
            congestion_scores.append({
                'team_name': team_name,
                'congestion_score': max(0.0, min(10.0, congestion_score))
            })
        
        # Create series
        congestion_df = pd.DataFrame(congestion_scores)
        if congestion_df.empty:
            return pd.Series(dtype=float)
        
        return pd.Series(
            congestion_df['congestion_score'].values,
            index=congestion_df['team_name'].values,
            name='fixture_congestion'
        )
    
    def _get_team_fixtures(self, fixtures_df: pd.DataFrame, team_name: str) -> pd.DataFrame:
        """Get upcoming fixtures for a specific team"""
        team_fixtures = fixtures_df[
            (fixtures_df['home_team_name'] == team_name) | 
            (fixtures_df['away_team_name'] == team_name)
        ].copy()
        
        # Sort by kickoff time
        team_fixtures = team_fixtures.sort_values('kickoff_time')
        
        return team_fixtures.head(10)  # Look at next 10 fixtures
    
    def _calculate_congestion_score(self, team_fixtures: pd.DataFrame) -> float:
        """Calculate congestion score based on fixture density"""
        if team_fixtures.empty:
            return 5.0  # Neutral congestion
        
        # Count fixtures per week
        fixtures_per_week = {}
        
        for _, fixture in team_fixtures.iterrows():
            gameweek = fixture.get('event', 0)
            if gameweek not in fixtures_per_week:
                fixtures_per_week[gameweek] = 0
            fixtures_per_week[gameweek] += 1
        
        # Calculate congestion penalty
        total_penalty = 0
        for gameweek, fixture_count in fixtures_per_week.items():
            if fixture_count > self.congestion_threshold:
                # Penalty for high fixture density
                penalty = (fixture_count - self.congestion_threshold) * self.rest_penalty
                total_penalty += penalty
        
        # Convert penalty to score (higher penalty = lower score)
        base_score = 5.0
        congestion_score = base_score - total_penalty
        
        return max(0.0, min(10.0, congestion_score))
    
    def validate(self, feature_values: pd.Series) -> bool:
        """Validate fixture congestion feature values"""
        if feature_values.empty:
            return False
        
        # Check for reasonable bounds (0-10 scale)
        if (feature_values < 0).any() or (feature_values > 10).any():
            return False
        
        return True


class HomeAwayBalanceFeature(TeamFeature):
    """Calculate home/away balance for teams"""
    
    description = "Team home/away balance in upcoming fixtures"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.home_preference = config.get('home_preference', 0.3)  # Bonus for home fixtures
    
    def calculate(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        """Calculate home/away balance for all teams"""
        teams_df = self.get_team_data(data)
        fixtures_df = self.get_fixture_data(data)
        
        if teams_df.empty or fixtures_df.empty:
            return pd.Series(dtype=float)
        
        balance_scores = []
        
        for _, team in teams_df.iterrows():
            team_name = team.get('name')
            if not team_name:
                continue
            
            # Get team's upcoming fixtures
            team_fixtures = self._get_team_fixtures(fixtures_df, team_name)
            
            if team_fixtures.empty:
                # No upcoming fixtures, use neutral score
                balance_score = 5.0
            else:
                # Calculate home/away balance
                balance_score = self._calculate_home_away_balance(team_fixtures)
            
            balance_scores.append({
                'team_name': team_name,
                'balance_score': max(0.0, min(10.0, balance_score))
            })
        
        # Create series
        balance_df = pd.DataFrame(balance_scores)
        if balance_df.empty:
            return pd.Series(dtype=float)
        
        return pd.Series(
            balance_df['balance_score'].values,
            index=balance_df['team_name'].values,
            name='home_away_balance'
        )
    
    def _get_team_fixtures(self, fixtures_df: pd.DataFrame, team_name: str) -> pd.DataFrame:
        """Get upcoming fixtures for a specific team"""
        team_fixtures = fixtures_df[
            (fixtures_df['home_team_name'] == team_name) | 
            (fixtures_df['away_team_name'] == team_name)
        ].copy()
        
        # Add home/away indicator
        team_fixtures['home_away'] = team_fixtures.apply(
            lambda row: 'H' if row['home_team_name'] == team_name else 'A', axis=1
        )
        
        # Sort by gameweek
        team_fixtures = team_fixtures.sort_values('event')
        
        return team_fixtures.head(5)  # Look at next 5 fixtures
    
    def _calculate_home_away_balance(self, team_fixtures: pd.DataFrame) -> float:
        """Calculate home/away balance score"""
        if team_fixtures.empty:
            return 5.0  # Neutral balance
        
        # Count home and away fixtures
        home_count = (team_fixtures['home_away'] == 'H').sum()
        away_count = (team_fixtures['home_away'] == 'A').sum()
        total_fixtures = len(team_fixtures)
        
        if total_fixtures == 0:
            return 5.0
        
        # Calculate balance (prefer more home fixtures)
        home_ratio = home_count / total_fixtures
        
        # Score based on home ratio (more home = higher score)
        balance_score = 5.0 + (home_ratio - 0.5) * 10.0  # Scale to 0-10
        
        return max(0.0, min(10.0, balance_score))
    
    def validate(self, feature_values: pd.Series) -> bool:
        """Validate home/away balance feature values"""
        if feature_values.empty:
            return False
        
        # Check for reasonable bounds (0-10 scale)
        if (feature_values < 0).any() or (feature_values > 10).any():
            return False
        
        return True 