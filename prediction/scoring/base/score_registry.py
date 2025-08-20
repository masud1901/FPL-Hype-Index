"""
Score Registry

This module provides a registry for managing and auto-discovering scoring classes.
The registry allows for dynamic loading and management of scores.
"""

from typing import Dict, List, Type, Optional, Any
import importlib
import inspect
from pathlib import Path

from .score_base import ScoreBase
from utils.logger import get_logger

logger = get_logger("score_registry")


class ScoreRegistry:
    """Registry for managing scoring classes"""

    def __init__(self):
        self._scores: Dict[str, Type[ScoreBase]] = {}
        self._score_instances: Dict[str, ScoreBase] = {}
        self._score_configs: Dict[str, Dict[str, Any]] = {}

    def register_score(
        self, score_class: Type[ScoreBase], config: Optional[Dict[str, Any]] = None
    ):
        """
        Register a score class

        Args:
            score_class: Score class to register
            config: Optional configuration for the score
        """
        if not issubclass(score_class, ScoreBase):
            raise ValueError(f"Score class must inherit from ScoreBase: {score_class}")

        score_name = score_class.__name__
        self._scores[score_name] = score_class

        if config:
            self._score_configs[score_name] = config.copy()

        logger.debug(f"Registered score: {score_name}")

    def unregister_score(self, score_name: str):
        """Unregister a score"""
        if score_name in self._scores:
            del self._scores[score_name]
            if score_name in self._score_instances:
                del self._score_instances[score_name]
            if score_name in self._score_configs:
                del self._score_configs[score_name]
            logger.debug(f"Unregistered score: {score_name}")

    def get_score_class(self, score_name: str) -> Optional[Type[ScoreBase]]:
        """Get a score class by name"""
        return self._scores.get(score_name)

    def get_score_instance(
        self, score_name: str, config: Optional[Dict[str, Any]] = None
    ) -> Optional[ScoreBase]:
        """
        Get or create a score instance

        Args:
            score_name: Name of the score
            config: Configuration for the score (overrides stored config)

        Returns:
            ScoreBase instance or None if not found
        """
        if score_name not in self._scores:
            logger.warning(f"Score not found: {score_name}")
            return None

        # Use provided config or stored config
        score_config = config or self._score_configs.get(score_name, {})

        # Create instance if not already created or config changed
        if (
            score_name not in self._score_instances
            or self._score_instances[score_name].config != score_config
        ):

            score_class = self._scores[score_name]
            self._score_instances[score_name] = score_class(score_config)

        return self._score_instances[score_name]

    def get_all_score_names(self) -> List[str]:
        """Get all registered score names"""
        return list(self._scores.keys())

    def get_scores_by_type(self, score_type: str) -> List[str]:
        """Get score names by type (position, composite, master)"""
        score_names = []
        for name, score_class in self._scores.items():
            # Create temporary instance to check type
            temp_instance = score_class({})
            if temp_instance.get_score_type() == score_type:
                score_names.append(name)
        return score_names

    def get_scores_by_position(self, position: str) -> List[str]:
        """Get position-specific score names for a position"""
        score_names = []
        for name, score_class in self._scores.items():
            # Create temporary instance to check position
            temp_instance = score_class({})
            if hasattr(
                temp_instance, "is_applicable_position"
            ) and temp_instance.is_applicable_position(position):
                score_names.append(name)
        return score_names

    def calculate_all_scores(self, data: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate all registered scores

        Args:
            data: Input data for score calculation

        Returns:
            Dict containing all calculated scores
        """
        results = {}

        for score_name in self.get_all_score_names():
            try:
                score_instance = self.get_score_instance(score_name)
                if score_instance:
                    score_value = score_instance.calculate_with_validation(data)
                    results[score_name] = score_value
                    logger.debug(f"Calculated score: {score_name} = {score_value:.2f}")

            except Exception as e:
                logger.error(f"Error calculating score {score_name}: {e}")
                results[score_name] = 0.0

        return results

    def calculate_scores_by_type(
        self, data: Dict[str, Any], score_type: str
    ) -> Dict[str, float]:
        """
        Calculate scores of a specific type

        Args:
            data: Input data for score calculation
            score_type: Type of scores to calculate ('position', 'composite', 'master')

        Returns:
            Dict containing calculated scores of the specified type
        """
        results = {}

        for score_name in self.get_scores_by_type(score_type):
            try:
                score_instance = self.get_score_instance(score_name)
                if score_instance:
                    score_value = score_instance.calculate_with_validation(data)
                    results[score_name] = score_value

            except Exception as e:
                logger.error(f"Error calculating score {score_name}: {e}")
                results[score_name] = 0.0

        return results

    def calculate_position_scores(
        self, data: Dict[str, Any], position: str
    ) -> Dict[str, float]:
        """
        Calculate position-specific scores for a position

        Args:
            data: Input data for score calculation
            position: Position to calculate scores for ('GK', 'DEF', 'MID', 'FWD')

        Returns:
            Dict containing calculated position-specific scores
        """
        results = {}

        for score_name in self.get_scores_by_position(position):
            try:
                score_instance = self.get_score_instance(score_name)
                if score_instance:
                    score_value = score_instance.calculate_with_validation(data)
                    results[score_name] = score_value

            except Exception as e:
                logger.error(f"Error calculating score {score_name}: {e}")
                results[score_name] = 0.0

        return results

    def get_score_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all registered scores"""
        info = {}

        for score_name, score_class in self._scores.items():
            try:
                # Create temporary instance to get info
                temp_instance = score_class({})
                info[score_name] = {
                    "class": score_class.__name__,
                    "type": temp_instance.get_score_type(),
                    "description": temp_instance.get_score_description(),
                    "config": self._score_configs.get(score_name, {}),
                    "position": (
                        getattr(temp_instance, "position", "ALL")
                        if hasattr(temp_instance, "position")
                        else "ALL"
                    ),
                }
            except Exception as e:
                logger.error(f"Error getting info for score {score_name}: {e}")
                info[score_name] = {"error": str(e)}

        return info

    def auto_discover_scores(self, module_paths: List[str]):
        """
        Auto-discover scores from module paths

        Args:
            module_paths: List of module paths to search for scores
        """
        for module_path in module_paths:
            try:
                module = importlib.import_module(module_path)

                # Find all classes in the module
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (
                        issubclass(obj, ScoreBase)
                        and obj != ScoreBase
                        and name not in self._scores
                    ):

                        self.register_score(obj)
                        logger.info(f"Auto-discovered score: {name} from {module_path}")

            except ImportError as e:
                logger.warning(f"Could not import module {module_path}: {e}")
            except Exception as e:
                logger.error(f"Error discovering scores from {module_path}: {e}")

    def clear(self):
        """Clear all registered scores"""
        self._scores.clear()
        self._score_instances.clear()
        self._score_configs.clear()
        logger.info("Cleared all registered scores")


# Global registry instance
score_registry = ScoreRegistry()
