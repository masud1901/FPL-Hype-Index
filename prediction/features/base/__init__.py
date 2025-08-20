"""
Base Feature Classes

This module contains abstract base classes and registries for feature engineering.
"""

from .feature_base import FeatureBase
from .feature_registry import FeatureRegistry

__all__ = ["FeatureBase", "FeatureRegistry"] 