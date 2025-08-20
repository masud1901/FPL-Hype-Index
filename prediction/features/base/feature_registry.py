"""
Feature Registry

This module provides a registry for managing and auto-discovering feature classes.
The registry allows for dynamic loading and management of features.
"""

from typing import Dict, List, Type, Optional, Any
import importlib
import inspect
from pathlib import Path

from .feature_base import FeatureBase
from utils.logger import get_logger

logger = get_logger("feature_registry")


class FeatureRegistry:
    """Registry for managing feature classes"""
    
    def __init__(self):
        self._features: Dict[str, Type[FeatureBase]] = {}
        self._feature_instances: Dict[str, FeatureBase] = {}
        self._feature_configs: Dict[str, Dict[str, Any]] = {}
    
    def register_feature(self, feature_class: Type[FeatureBase], 
                        config: Optional[Dict[str, Any]] = None):
        """
        Register a feature class
        
        Args:
            feature_class: Feature class to register
            config: Optional configuration for the feature
        """
        if not issubclass(feature_class, FeatureBase):
            raise ValueError(f"Feature class must inherit from FeatureBase: {feature_class}")
        
        feature_name = feature_class.__name__
        self._features[feature_name] = feature_class
        
        if config:
            self._feature_configs[feature_name] = config.copy()
        
        logger.debug(f"Registered feature: {feature_name}")
    
    def unregister_feature(self, feature_name: str):
        """Unregister a feature"""
        if feature_name in self._features:
            del self._features[feature_name]
            if feature_name in self._feature_instances:
                del self._feature_instances[feature_name]
            if feature_name in self._feature_configs:
                del self._feature_configs[feature_name]
            logger.debug(f"Unregistered feature: {feature_name}")
    
    def get_feature_class(self, feature_name: str) -> Optional[Type[FeatureBase]]:
        """Get a feature class by name"""
        return self._features.get(feature_name)
    
    def get_feature_instance(self, feature_name: str, 
                           config: Optional[Dict[str, Any]] = None) -> Optional[FeatureBase]:
        """
        Get or create a feature instance
        
        Args:
            feature_name: Name of the feature
            config: Configuration for the feature (overrides stored config)
            
        Returns:
            FeatureBase instance or None if not found
        """
        if feature_name not in self._features:
            logger.warning(f"Feature not found: {feature_name}")
            return None
        
        # Use provided config or stored config
        feature_config = config or self._feature_configs.get(feature_name, {})
        
        # Create instance if not already created or config changed
        if (feature_name not in self._feature_instances or 
            self._feature_instances[feature_name].config != feature_config):
            
            feature_class = self._features[feature_name]
            self._feature_instances[feature_name] = feature_class(feature_config)
        
        return self._feature_instances[feature_name]
    
    def get_all_feature_names(self) -> List[str]:
        """Get all registered feature names"""
        return list(self._features.keys())
    
    def get_features_by_type(self, feature_type: str) -> List[str]:
        """Get feature names by type (player, team, contextual)"""
        feature_names = []
        for name, feature_class in self._features.items():
            # Create temporary instance to check type
            temp_instance = feature_class({})
            if temp_instance.get_feature_type() == feature_type:
                feature_names.append(name)
        return feature_names
    
    def auto_discover_features(self, module_paths: List[str]):
        """
        Auto-discover features from module paths
        
        Args:
            module_paths: List of module paths to search for features
        """
        for module_path in module_paths:
            try:
                module = importlib.import_module(module_path)
                
                # Find all classes in the module
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (issubclass(obj, FeatureBase) and 
                        obj != FeatureBase and 
                        name not in self._features):
                        
                        self.register_feature(obj)
                        logger.info(f"Auto-discovered feature: {name} from {module_path}")
                        
            except ImportError as e:
                logger.warning(f"Could not import module {module_path}: {e}")
            except Exception as e:
                logger.error(f"Error discovering features from {module_path}: {e}")
    
    def discover_features_from_directory(self, directory_path: str):
        """
        Discover features from a directory structure
        
        Args:
            directory_path: Path to directory containing feature modules
        """
        directory = Path(directory_path)
        if not directory.exists():
            logger.warning(f"Directory does not exist: {directory_path}")
            return
        
        # Find all Python files in the directory
        python_files = directory.rglob("*.py")
        
        for python_file in python_files:
            # Convert file path to module path
            relative_path = python_file.relative_to(directory)
            module_parts = list(relative_path.parent.parts) + [relative_path.stem]
            
            # Skip __init__.py files
            if "__init__" in module_parts:
                continue
            
            # Convert to module path
            module_path = ".".join(module_parts)
            
            try:
                # Import the module
                module = importlib.import_module(module_path)
                
                # Find feature classes
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (issubclass(obj, FeatureBase) and 
                        obj != FeatureBase and 
                        name not in self._features):
                        
                        self.register_feature(obj)
                        logger.info(f"Discovered feature: {name} from {module_path}")
                        
            except ImportError as e:
                logger.debug(f"Could not import {module_path}: {e}")
            except Exception as e:
                logger.error(f"Error discovering features from {module_path}: {e}")
    
    def calculate_all_features(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate all registered features
        
        Args:
            data: Input data for feature calculation
            
        Returns:
            Dict containing all calculated features
        """
        results = {}
        
        for feature_name in self.get_all_feature_names():
            try:
                feature_instance = self.get_feature_instance(feature_name)
                if feature_instance:
                    feature_values = feature_instance.calculate_with_validation(data)
                    results[feature_name] = feature_values
                    logger.debug(f"Calculated feature: {feature_name}")
                    
            except Exception as e:
                logger.error(f"Error calculating feature {feature_name}: {e}")
                results[feature_name] = None
        
        return results
    
    def calculate_features_by_type(self, data: Dict[str, Any], 
                                 feature_type: str) -> Dict[str, Any]:
        """
        Calculate features of a specific type
        
        Args:
            data: Input data for feature calculation
            feature_type: Type of features to calculate ('player', 'team', 'contextual')
            
        Returns:
            Dict containing calculated features of the specified type
        """
        results = {}
        
        for feature_name in self.get_features_by_type(feature_type):
            try:
                feature_instance = self.get_feature_instance(feature_name)
                if feature_instance:
                    feature_values = feature_instance.calculate_with_validation(data)
                    results[feature_name] = feature_values
                    
            except Exception as e:
                logger.error(f"Error calculating feature {feature_name}: {e}")
                results[feature_name] = None
        
        return results
    
    def get_feature_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all registered features"""
        info = {}
        
        for feature_name, feature_class in self._features.items():
            try:
                # Create temporary instance to get info
                temp_instance = feature_class({})
                info[feature_name] = {
                    'class': feature_class.__name__,
                    'type': temp_instance.get_feature_type(),
                    'description': temp_instance.get_feature_description(),
                    'config': self._feature_configs.get(feature_name, {})
                }
            except Exception as e:
                logger.error(f"Error getting info for feature {feature_name}: {e}")
                info[feature_name] = {'error': str(e)}
        
        return info
    
    def clear(self):
        """Clear all registered features"""
        self._features.clear()
        self._feature_instances.clear()
        self._feature_configs.clear()
        logger.info("Cleared all registered features")


# Global registry instance
feature_registry = FeatureRegistry() 