"""
Feature Base Classes

This module contains abstract base classes for feature engineering.
All features must inherit from FeatureBase and implement the required methods.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime

from utils.logger import get_logger

logger = get_logger("feature_base")


class FeatureBase(ABC):
    """Abstract base class for all features"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = self.__class__.__name__
        self.description = getattr(self, "description", f"Feature: {self.name}")
        self.feature_type = getattr(
            self, "feature_type", "player"
        )  # 'player', 'team', 'contextual'

    @abstractmethod
    def calculate(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        """
        Calculate feature values for players/teams

        Args:
            data: Dictionary containing DataFrames with keys like 'players', 'fixtures', 'teams'

        Returns:
            pd.Series: Feature values indexed by player_id or team_id
        """
        pass

    @abstractmethod
    def validate(self, feature_values: pd.Series) -> bool:
        """
        Validate calculated feature values

        Args:
            feature_values: Series containing calculated feature values

        Returns:
            bool: True if values are valid, False otherwise
        """
        pass

    def get_feature_name(self) -> str:
        """Get the feature name for use in DataFrames"""
        return self.name.lower()

    def get_feature_description(self) -> str:
        """Get feature description"""
        return self.description

    def get_feature_type(self) -> str:
        """Get feature type (player, team, contextual)"""
        return self.feature_type

    def preprocess_data(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        Preprocess data before feature calculation

        Args:
            data: Raw data dictionary

        Returns:
            Dict[str, pd.DataFrame]: Preprocessed data
        """
        # Default implementation - no preprocessing
        return data

    def postprocess_feature(self, feature_values: pd.Series) -> pd.Series:
        """
        Postprocess feature values after calculation

        Args:
            feature_values: Raw feature values

        Returns:
            pd.Series: Postprocessed feature values
        """
        # Default implementation - no postprocessing
        return feature_values

    def handle_missing_data(self, feature_values: pd.Series) -> pd.Series:
        """
        Handle missing data in feature values

        Args:
            feature_values: Feature values with potential missing data

        Returns:
            pd.Series: Feature values with missing data handled
        """
        # Default implementation - fill with 0
        return feature_values.fillna(0)

    def normalize_feature(self, feature_values: pd.Series) -> pd.Series:
        """
        Normalize feature values to 0-10 scale

        Args:
            feature_values: Raw feature values

        Returns:
            pd.Series: Normalized feature values (0-10 scale)
        """
        if feature_values.empty:
            return feature_values

        # Handle edge cases
        if feature_values.min() == feature_values.max():
            return pd.Series(5.0, index=feature_values.index)

        # Min-max normalization to 0-10 scale
        normalized = (
            (feature_values - feature_values.min())
            / (feature_values.max() - feature_values.min())
        ) * 10

        return normalized

    def calculate_with_validation(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        """
        Calculate feature with full validation pipeline

        Args:
            data: Input data dictionary

        Returns:
            pd.Series: Validated and processed feature values
        """
        try:
            # Preprocess data
            processed_data = self.preprocess_data(data)

            # Calculate feature
            feature_values = self.calculate(processed_data)

            # Handle missing data
            feature_values = self.handle_missing_data(feature_values)

            # Postprocess feature
            feature_values = self.postprocess_feature(feature_values)

            # Validate feature
            if not self.validate(feature_values):
                logger.warning(f"Feature validation failed for {self.name}")
                # Return default values if validation fails
                return pd.Series(0.0, index=feature_values.index)

            logger.debug(f"Successfully calculated feature: {self.name}")
            return feature_values

        except Exception as e:
            logger.error(f"Error calculating feature {self.name}: {e}")
            # Return empty series on error
            return pd.Series(dtype=float)

    def get_config(self) -> Dict[str, Any]:
        """Get feature configuration"""
        return self.config.copy()

    def update_config(self, new_config: Dict[str, Any]):
        """Update feature configuration"""
        self.config.update(new_config)

    def __str__(self) -> str:
        return f"{self.name} ({self.feature_type})"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(config={self.config})"


class PlayerFeature(FeatureBase):
    """Base class for player-specific features"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.feature_type = "player"

    def get_player_data(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Get player data from input data dictionary"""
        return data.get("players", pd.DataFrame())

    def get_player_history(
        self, data: Dict[str, pd.DataFrame], player_id: int
    ) -> pd.DataFrame:
        """Get player history data (placeholder for future enhancement)"""
        # This would be implemented to get player history from the data
        return pd.DataFrame()

    def get_fixture_data(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Get fixture data from input data dictionary"""
        return data.get("fixtures", pd.DataFrame())

    def validate(self, feature_values: pd.Series) -> bool:
        """Default validation for player features"""
        if feature_values.empty:
            return False

        # Check for reasonable bounds (0-10 scale)
        if (feature_values < 0).any() or (feature_values > 10).any():
            return False

        return True


class TeamFeature(FeatureBase):
    """Base class for team-specific features"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.feature_type = "team"

    def get_team_data(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Get team data from input data dictionary"""
        return data.get("teams", pd.DataFrame())

    def get_team_fixtures(
        self, data: Dict[str, pd.DataFrame], team_name: str
    ) -> pd.DataFrame:
        """Get fixtures for a specific team"""
        fixtures_df = data.get("fixtures", pd.DataFrame())
        if fixtures_df.empty:
            return pd.DataFrame()

        # Filter fixtures for the team
        team_fixtures = fixtures_df[
            (fixtures_df["home_team_name"] == team_name)
            | (fixtures_df["away_team_name"] == team_name)
        ]

        return team_fixtures

    def get_fixture_data(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Get fixture data from input data dictionary"""
        return data.get("fixtures", pd.DataFrame())

    def validate(self, feature_values: pd.Series) -> bool:
        """Default validation for team features"""
        if feature_values.empty:
            return False

        # Check for reasonable bounds (0-10 scale)
        if (feature_values < 0).any() or (feature_values > 10).any():
            return False

        return True


class ContextualFeature(FeatureBase):
    """Base class for contextual features (fixtures, weather, etc.)"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.feature_type = "contextual"

    def get_fixture_data(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Get fixture data from input data dictionary"""
        return data.get("fixtures", pd.DataFrame())

    def validate(self, feature_values: pd.Series) -> bool:
        """Default validation for contextual features"""
        if feature_values.empty:
            return False

        # Check for reasonable bounds (0-10 scale)
        if (feature_values < 0).any() or (feature_values > 10).any():
            return False

        return True
