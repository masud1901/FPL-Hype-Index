"""
Fixture Features

This module contains features related to fixture difficulty and scheduling.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List

from ..base.feature_base import PlayerFeature
from utils.logger import get_logger

logger = get_logger("fixture_features")


class FixtureDifficultyFeature(PlayerFeature):
    """Calculate fixture difficulty for players"""
    
    description = "Player fixture difficulty based on upcoming opponents and home/away"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.lookahead_gameweeks = config.get('lookahead_gameweeks', 5)
        self.home_advantage = config.get('home_advantage', 0.5)
        self.away_penalty = config.get('away_penalty', -0.5)
    
    def calculate(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        """Calculate fixture difficulty for all players"""
        players_df = self.get_player_data(data)
        fixtures_df = self.get_fixture_data(data)
        teams_df = data.get('teams', pd.DataFrame())
        
        if players_df.empty or fixtures_df.empty:
            return pd.Series(dtype=float)
        
        fixture_scores = []
        
        for _, player in players_df.iterrows():
            player_id = player.get('id')
            team_name = player.get('team')
            
            if not player_id or not team_name:
                continue
            
            # Get player's upcoming fixtures
            player_fixtures = self._get_player_fixtures(fixtures_df, team_name)
            
            if player_fixtures.empty:
                # No upcoming fixtures, use neutral score
                fixture_score = 5.0
            else:
                # Calculate fixture difficulty
                fixture_score = self._calculate_fixture_difficulty(player_fixtures, teams_df)
            
            fixture_scores.append({
                'player_id': player_id,
                'fixture_score': max(0.0, min(10.0, fixture_score))
            })
        
        # Create series
        fixture_df = pd.DataFrame(fixture_scores)
        if fixture_df.empty:
            return pd.Series(dtype=float)
        
        return pd.Series(
            fixture_df['fixture_score'].values,
            index=fixture_df['player_id'].values,
            name='fixture_difficulty'
        )
    
    def _get_player_fixtures(self, fixtures_df: pd.DataFrame, team_name: str) -> pd.DataFrame:
        """Get upcoming fixtures for a player's team"""
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
    
    def _calculate_fixture_difficulty(self, player_fixtures: pd.DataFrame, teams_df: pd.DataFrame) -> float:
        """Calculate overall fixture difficulty for a player"""
        if player_fixtures.empty:
            return 5.0  # Neutral difficulty
        
        fixture_difficulties = []
        
        for _, fixture in player_fixtures.iterrows():
            difficulty = self._calculate_single_fixture_difficulty(fixture, teams_df)
            fixture_difficulties.append(difficulty)
        
        # Calculate weighted average (earlier fixtures weighted more)
        weights = self._get_fixture_weights(len(fixture_difficulties))
        weighted_difficulty = sum(d * w for d, w in zip(fixture_difficulties, weights))
        
        return weighted_difficulty
    
    def _calculate_single_fixture_difficulty(self, fixture: pd.Series, teams_df: pd.DataFrame) -> float:
        """Calculate difficulty for a single fixture"""
        home_away = fixture.get('home_away', 'H')
        
        # Get opponent strength
        if home_away == 'H':
            opponent_name = fixture.get('away_team_name')
            opponent_strength = fixture.get('away_team_strength', 50.0)
        else:
            opponent_name = fixture.get('home_team_name')
            opponent_strength = fixture.get('home_team_strength', 50.0)
        
        # Get opponent team data for additional metrics
        opponent_team = teams_df[teams_df['name'] == opponent_name]
        if not opponent_team.empty:
            opponent_form = opponent_team.iloc[0].get('form', 50.0)
            opponent_position = opponent_team.iloc[0].get('position', 10)
        else:
            opponent_form = 50.0
            opponent_position = 10
        
        # Base difficulty (higher = easier fixture)
        base_difficulty = 10.0 - (opponent_strength / 10.0)
        
        # Apply home/away adjustment
        if home_away == 'H':
            base_difficulty += self.home_advantage
        else:
            base_difficulty += self.away_penalty
        
        # Apply opponent form adjustment
        form_adjustment = (opponent_form - 50.0) / 100.0
        base_difficulty -= form_adjustment  # Better opponent form = harder fixture
        
        # Apply opponent position adjustment (lower position = better team)
        position_adjustment = (opponent_position - 10.0) / 20.0
        base_difficulty += position_adjustment  # Lower position = easier fixture
        
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
        """Validate fixture difficulty feature values"""
        if feature_values.empty:
            return False
        
        # Check for reasonable bounds (0-10 scale)
        if (feature_values < 0).any() or (feature_values > 10).any():
            return False
        
        return True


class FixtureRunFeature(PlayerFeature):
    """Calculate fixture run difficulty (consecutive fixtures)"""
    
    description = "Player fixture run difficulty based on consecutive fixture difficulty"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.run_length = config.get('run_length', 3)
        self.difficulty_threshold = config.get('difficulty_threshold', 7.0)
    
    def calculate(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        """Calculate fixture run difficulty for all players"""
        players_df = self.get_player_data(data)
        fixtures_df = self.get_fixture_data(data)
        teams_df = data.get('teams', pd.DataFrame())
        
        if players_df.empty or fixtures_df.empty:
            return pd.Series(dtype=float)
        
        run_scores = []
        
        for _, player in players_df.iterrows():
            player_id = player.get('id')
            team_name = player.get('team')
            
            if not player_id or not team_name:
                continue
            
            # Get player's upcoming fixtures
            player_fixtures = self._get_player_fixtures(fixtures_df, team_name)
            
            if player_fixtures.empty:
                # No upcoming fixtures, use neutral score
                run_score = 5.0
            else:
                # Calculate fixture run difficulty
                run_score = self._calculate_fixture_run_difficulty(player_fixtures, teams_df)
            
            run_scores.append({
                'player_id': player_id,
                'run_score': max(0.0, min(10.0, run_score))
            })
        
        # Create series
        run_df = pd.DataFrame(run_scores)
        if run_df.empty:
            return pd.Series(dtype=float)
        
        return pd.Series(
            run_df['run_score'].values,
            index=run_df['player_id'].values,
            name='fixture_run_difficulty'
        )
    
    def _get_player_fixtures(self, fixtures_df: pd.DataFrame, team_name: str) -> pd.DataFrame:
        """Get upcoming fixtures for a player's team"""
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
        
        return team_fixtures.head(self.run_length)
    
    def _calculate_fixture_run_difficulty(self, player_fixtures: pd.DataFrame, teams_df: pd.DataFrame) -> float:
        """Calculate fixture run difficulty"""
        if player_fixtures.empty:
            return 5.0  # Neutral difficulty
        
        # Calculate individual fixture difficulties
        fixture_difficulties = []
        for _, fixture in player_fixtures.iterrows():
            difficulty = self._calculate_single_fixture_difficulty(fixture, teams_df)
            fixture_difficulties.append(difficulty)
        
        # Calculate run difficulty
        if len(fixture_difficulties) < self.run_length:
            # Not enough fixtures for a full run
            avg_difficulty = np.mean(fixture_difficulties)
            return avg_difficulty
        
        # Check for easy run (all fixtures above threshold)
        easy_run = all(d >= self.difficulty_threshold for d in fixture_difficulties)
        if easy_run:
            return 8.0  # Bonus for easy run
        
        # Check for hard run (all fixtures below threshold)
        hard_run = all(d < self.difficulty_threshold for d in fixture_difficulties)
        if hard_run:
            return 2.0  # Penalty for hard run
        
        # Mixed difficulty run
        return np.mean(fixture_difficulties)
    
    def _calculate_single_fixture_difficulty(self, fixture: pd.Series, teams_df: pd.DataFrame) -> float:
        """Calculate difficulty for a single fixture (simplified version)"""
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
            base_difficulty += 0.5
        else:
            base_difficulty -= 0.5
        
        return max(1.0, min(10.0, base_difficulty))
    
    def validate(self, feature_values: pd.Series) -> bool:
        """Validate fixture run feature values"""
        if feature_values.empty:
            return False
        
        # Check for reasonable bounds (0-10 scale)
        if (feature_values < 0).any() or (feature_values > 10).any():
            return False
        
        return True 