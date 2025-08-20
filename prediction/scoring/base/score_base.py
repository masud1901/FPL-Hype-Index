"""
Score Base Classes

This module contains abstract base classes for scoring algorithms.
All scoring algorithms must inherit from ScoreBase and implement the required methods.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime

from utils.logger import get_logger

logger = get_logger("score_base")


class ScoreBase(ABC):
    """Abstract base class for all scoring algorithms"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = self.__class__.__name__
        self.description = getattr(self, "description", f"Score: {self.name}")
        self.score_type = getattr(
            self, "score_type", "composite"
        )  # 'position', 'composite', 'master'

    @abstractmethod
    def calculate_score(self, data: Dict[str, Any]) -> float:
        """
        Calculate score for a single entity (player/team)

        Args:
            data: Dictionary containing data for the entity

        Returns:
            float: Score value (typically 0-10 scale)
        """
        pass

    @abstractmethod
    def validate_score(self, score: float) -> bool:
        """
        Validate calculated score

        Args:
            score: Score value to validate

        Returns:
            bool: True if score is valid, False otherwise
        """
        pass

    def get_score_name(self) -> str:
        """Get the score name for use in DataFrames"""
        return self.name.lower()

    def get_score_description(self) -> str:
        """Get score description"""
        return self.description

    def get_score_type(self) -> str:
        """Get score type (position, composite, master)"""
        return self.score_type

    def preprocess_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preprocess data before score calculation

        Args:
            data: Raw data dictionary

        Returns:
            Dict[str, Any]: Preprocessed data
        """
        # Default implementation - no preprocessing
        return data

    def postprocess_score(self, score: float) -> float:
        """
        Postprocess score after calculation

        Args:
            score: Raw score value

        Returns:
            float: Postprocessed score value
        """
        # Default implementation - no postprocessing
        return score

    def normalize_score(self, score: float) -> float:
        """
        Normalize score to 0-10 scale

        Args:
            score: Raw score value

        Returns:
            float: Normalized score value (0-10 scale)
        """
        return max(0.0, min(10.0, score))

    def calculate_with_validation(self, data: Dict[str, Any]) -> float:
        """
        Calculate score with full validation pipeline

        Args:
            data: Input data dictionary

        Returns:
            float: Validated and processed score value
        """
        try:
            # Preprocess data
            processed_data = self.preprocess_data(data)

            # Calculate score
            score = self.calculate_score(processed_data)

            # Handle missing/invalid scores
            if score is None or np.isnan(score):
                logger.warning(f"Invalid score calculated for {self.name}")
                return 0.0

            # Postprocess score
            score = self.postprocess_score(score)

            # Normalize score
            score = self.normalize_score(score)

            # Validate score
            if not self.validate_score(score):
                logger.warning(f"Score validation failed for {self.name}")
                return 0.0

            logger.debug(f"Successfully calculated score: {self.name} = {score:.2f}")
            return score

        except Exception as e:
            logger.error(f"Error calculating score {self.name}: {e}")
            return 0.0

    def get_config(self) -> Dict[str, Any]:
        """Get score configuration"""
        return self.config.copy()

    def update_config(self, new_config: Dict[str, Any]):
        """Update score configuration"""
        self.config.update(new_config)

    def __str__(self) -> str:
        return f"{self.name} ({self.score_type})"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(config={self.config})"


class PlayerScore(ScoreBase):
    """Base class for player-specific scoring algorithms"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.score_type = "player"

    def get_player_stats(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract player statistics from data"""
        # Default implementation - return data as is
        return data

    def validate_score(self, score: float) -> bool:
        """Default validation for player scores"""
        if score is None or np.isnan(score):
            return False

        # Check for reasonable bounds (0-10 scale)
        if score < 0 or score > 10:
            return False

        return True


class PositionSpecificScore(PlayerScore):
    """Base class for position-specific scoring algorithms"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.score_type = "position"
        self.position = getattr(self, "position", "ALL")

    def get_position(self) -> str:
        """Get the position this score is designed for"""
        return self.position

    def is_applicable_position(self, position: str) -> bool:
        """Check if this score is applicable for a given position"""
        return self.position == "ALL" or position.upper() == self.position.upper()


class CompositeScore(ScoreBase):
    """Base class for composite scoring algorithms"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.score_type = "composite"
        self.component_weights = config.get("component_weights", {})

    def get_component_weights(self) -> Dict[str, float]:
        """Get weights for score components"""
        return self.component_weights.copy()

    def calculate_weighted_score(self, components: Dict[str, float]) -> float:
        """Calculate weighted composite score from components"""
        if not components:
            return 0.0

        # If no weights provided, use equal weights
        if not self.component_weights:
            return sum(components.values()) / len(components)

        # Calculate weighted sum
        weighted_sum = 0.0
        total_weight = 0.0

        for component, value in components.items():
            weight = self.component_weights.get(component, 0.0)
            weighted_sum += value * weight
            total_weight += weight

        # Normalize by total weight
        if total_weight > 0:
            return weighted_sum / total_weight
        else:
            return 0.0

    def validate_score(self, score: float) -> bool:
        """Default validation for composite scores"""
        if score is None or np.isnan(score):
            return False

        # Check for reasonable bounds (0-10 scale)
        if score < 0 or score > 10:
            return False

        return True


class MasterScore(ScoreBase):
    """Base class for master scoring algorithms"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.score_type = "master"
        self.sub_score_weights = config.get("sub_score_weights", {})
        self.interaction_bonuses = config.get("interaction_bonuses", {})
        self.risk_penalties = config.get("risk_penalties", {})

    def calculate_base_score(self, sub_scores: Dict[str, float]) -> float:
        """Calculate base score from sub-scores"""
        return self.calculate_weighted_score(sub_scores, self.sub_score_weights)

    def calculate_interaction_bonus(self, sub_scores: Dict[str, float]) -> float:
        """Calculate interaction bonus between sub-scores"""
        # Default implementation - no interaction bonus
        return 0.0

    def calculate_risk_penalty(self, data: Dict[str, Any]) -> float:
        """Calculate risk penalty based on player/team risk factors"""
        # Default implementation - no risk penalty
        return 0.0

    def calculate_confidence_multiplier(self, data: Dict[str, Any]) -> float:
        """Calculate confidence multiplier based on data quality"""
        # Default implementation - full confidence
        return 1.0

    def calculate_weighted_score(
        self, scores: Dict[str, float], weights: Dict[str, float]
    ) -> float:
        """Calculate weighted score from multiple scores"""
        if not scores:
            return 0.0

        # If no weights provided, use equal weights
        if not weights:
            return sum(scores.values()) / len(scores)

        # Calculate weighted sum
        weighted_sum = 0.0
        total_weight = 0.0

        for score_name, value in scores.items():
            weight = weights.get(score_name, 0.0)
            weighted_sum += value * weight
            total_weight += weight

        # Normalize by total weight
        if total_weight > 0:
            return weighted_sum / total_weight
        else:
            return 0.0

    def validate_score(self, score: float) -> bool:
        """Default validation for master scores"""
        if score is None or np.isnan(score):
            return False

        # Master scores can potentially exceed 10 due to bonuses
        if score < 0 or score > 15:
            return False

        return True
