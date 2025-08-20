"""
Scoring Weights Configuration

This module contains all weights and parameters for the scoring algorithms.
Weights are optimized based on historical performance and can be adjusted
without changing the core algorithm logic.
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class ScoringWeights:
    """Configuration for scoring algorithm weights"""
    
    # Position-specific weights for PIS calculation
    goalkeeper_weights = {
        'aqs': 0.35,  # Advanced Quality Score
        'fcs': 0.25,  # Form Consistency Score
        'tms': 0.20,  # Team Momentum Score
        'fxs': 0.15,  # Fixture Score
        'vs': 0.05    # Value Score
    }
    
    defender_weights = {
        'aqs': 0.30,
        'fcs': 0.25,
        'tms': 0.20,
        'fxs': 0.20,
        'vs': 0.05
    }
    
    midfielder_weights = {
        'aqs': 0.30,
        'fcs': 0.25,
        'tms': 0.15,
        'fxs': 0.20,
        'vs': 0.10
    }
    
    forward_weights = {
        'aqs': 0.35,
        'fcs': 0.25,
        'tms': 0.15,
        'fxs': 0.15,
        'vs': 0.10
    }
    
    # Interaction bonus thresholds
    interaction_thresholds = {
        'high_form': 7.0,
        'easy_fixtures': 7.0,
        'high_quality': 7.0,
        'good_momentum': 7.0,
        'high_value': 7.0
    }
    
    # Interaction bonus values
    interaction_bonuses = {
        'form_fixture': 0.5,    # High form + easy fixtures
        'quality_momentum': 0.3, # High quality + team momentum
        'value_form': 0.2       # High value + good form
    }
    
    # Risk penalty factors
    risk_factors = {
        'injury_history': 0.3,
        'rotation_risk': 0.2,
        'fixture_congestion': 0.1,
        'age_risk': 0.1
    }
    
    # Form calculation parameters
    form_parameters = {
        'lookback_gameweeks': 6,
        'weights': [0.3, 0.25, 0.2, 0.15, 0.08, 0.02],  # Most recent first
        'volatility_penalty_threshold': 1.0,
        'ceiling_bonus_threshold': 8.0
    }
    
    # Fixture difficulty parameters
    fixture_parameters = {
        'lookahead_gameweeks': 5,
        'home_advantage': 0.5,
        'away_penalty': -0.5,
        'difficulty_multipliers': {
            'very_easy': 1.2,
            'easy': 1.1,
            'medium': 1.0,
            'hard': 0.9,
            'very_hard': 0.8
        }
    }
    
    # Value calculation parameters
    value_parameters = {
        'points_per_million_threshold': 20,
        'price_efficiency_weight': 0.7,
        'ownership_penalty': 0.1
    }
    
    # Team momentum parameters
    momentum_parameters = {
        'recent_results_weight': 0.4,
        'goal_difference_weight': 0.3,
        'expected_performance_weight': 0.3,
        'lookback_gameweeks': 5
    }
    
    # Quality score parameters
    quality_parameters = {
        'goalkeeper': {
            'save_performance': 0.4,
            'clean_sheet_potential': 0.3,
            'distribution_quality': 0.2,
            'bonus_potential': 0.1
        },
        'defender': {
            'clean_sheet_potential': 0.4,
            'attacking_returns': 0.3,
            'defensive_actions': 0.2,
            'bonus_potential': 0.1
        },
        'midfielder': {
            'goal_threat': 0.3,
            'creativity': 0.3,
            'defensive_contribution': 0.2,
            'bonus_potential': 0.2
        },
        'forward': {
            'finishing': 0.4,
            'goal_threat': 0.3,
            'assist_potential': 0.2,
            'bonus_potential': 0.1
        }
    }
    
    def get_position_weights(self, position: str) -> Dict[str, float]:
        """Get weights for a specific position"""
        position_map = {
            'GK': self.goalkeeper_weights,
            'DEF': self.defender_weights,
            'MID': self.midfielder_weights,
            'FWD': self.forward_weights
        }
        return position_map.get(position, self.midfielder_weights)
    
    def get_quality_weights(self, position: str) -> Dict[str, float]:
        """Get quality score weights for a specific position"""
        return self.quality_parameters.get(position.lower(), self.quality_parameters['midfielder'])


# Global instance
scoring_weights = ScoringWeights() 