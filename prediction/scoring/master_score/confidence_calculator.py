"""
Confidence Calculator

This module contains the confidence calculator that provides confidence scores
for Player Impact Score predictions.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from utils.logger import get_logger

logger = get_logger("confidence_calculator")


class ConfidenceCalculator:
    """Confidence calculator for Player Impact Score predictions"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Confidence factors
        self.data_quality_weight = config.get('data_quality_weight', 0.3)
        self.sample_size_weight = config.get('sample_size_weight', 0.25)
        self.consistency_weight = config.get('consistency_weight', 0.25)
        self.model_confidence_weight = config.get('model_confidence_weight', 0.2)
        
        # Thresholds
        self.high_confidence_threshold = config.get('high_confidence_threshold', 0.8)
        self.medium_confidence_threshold = config.get('medium_confidence_threshold', 0.6)
        self.low_confidence_threshold = config.get('low_confidence_threshold', 0.4)
    
    def calculate_confidence(self, data: Dict[str, Any], sub_scores: Dict[str, float], 
                           pis_score: float) -> Dict[str, Any]:
        """Calculate comprehensive confidence score for a prediction"""
        
        # Calculate individual confidence components
        data_quality = self._calculate_data_quality_confidence(data)
        sample_size = self._calculate_sample_size_confidence(data)
        consistency = self._calculate_consistency_confidence(sub_scores)
        model_confidence = self._calculate_model_confidence(data, pis_score)
        
        # Weighted combination
        total_confidence = (
            data_quality * self.data_quality_weight +
            sample_size * self.sample_size_weight +
            consistency * self.consistency_weight +
            model_confidence * self.model_confidence_weight
        )
        
        # Determine confidence level
        confidence_level = self._get_confidence_level(total_confidence)
        
        # Calculate confidence intervals
        confidence_intervals = self._calculate_confidence_intervals(pis_score, total_confidence)
        
        return {
            'total_confidence': total_confidence,
            'confidence_level': confidence_level,
            'components': {
                'data_quality': data_quality,
                'sample_size': sample_size,
                'consistency': consistency,
                'model_confidence': model_confidence
            },
            'confidence_intervals': confidence_intervals,
            'weights': {
                'data_quality_weight': self.data_quality_weight,
                'sample_size_weight': self.sample_size_weight,
                'consistency_weight': self.consistency_weight,
                'model_confidence_weight': self.model_confidence_weight
            }
        }
    
    def _calculate_data_quality_confidence(self, data: Dict[str, Any]) -> float:
        """Calculate confidence based on data quality"""
        # Check for missing or invalid data
        required_fields = [
            'total_points', 'form', 'price', 'selected_by_percent',
            'goals_scored', 'assists', 'clean_sheets', 'bonus'
        ]
        
        missing_fields = 0
        invalid_fields = 0
        
        for field in required_fields:
            if field not in data:
                missing_fields += 1
            elif data[field] is None:
                missing_fields += 1
            elif isinstance(data[field], (int, float)) and data[field] < 0:
                invalid_fields += 1
        
        # Calculate quality score
        total_fields = len(required_fields)
        quality_score = 1.0 - ((missing_fields + invalid_fields) / total_fields)
        
        # Additional quality checks
        if data.get('played', 0) == 0:
            quality_score *= 0.5  # Penalty for no games played
        
        # Check for reasonable data ranges
        if data.get('total_points', 0) > 500:  # Unrealistic total points
            quality_score *= 0.8
        
        if data.get('price', 0) > 20:  # Unrealistic price
            quality_score *= 0.9
        
        return max(0.0, min(1.0, quality_score))
    
    def _calculate_sample_size_confidence(self, data: Dict[str, Any]) -> float:
        """Calculate confidence based on sample size (games played)"""
        played = data.get('played', 1)
        
        # More games = higher confidence
        if played >= 25:
            confidence = 1.0
        elif played >= 20:
            confidence = 0.95
        elif played >= 15:
            confidence = 0.9
        elif played >= 10:
            confidence = 0.8
        elif played >= 5:
            confidence = 0.7
        elif played >= 3:
            confidence = 0.6
        elif played >= 1:
            confidence = 0.5
        else:
            confidence = 0.3
        
        return confidence
    
    def _calculate_consistency_confidence(self, sub_scores: Dict[str, float]) -> float:
        """Calculate confidence based on consistency across sub-scores"""
        if not sub_scores:
            return 0.5
        
        values = list(sub_scores.values())
        
        # Calculate coefficient of variation
        mean_score = np.mean(values)
        std_score = np.std(values)
        
        if mean_score == 0:
            return 0.5
        
        cv = std_score / mean_score
        
        # Lower CV = higher consistency = higher confidence
        if cv <= 0.15:
            confidence = 1.0
        elif cv <= 0.25:
            confidence = 0.9
        elif cv <= 0.35:
            confidence = 0.8
        elif cv <= 0.45:
            confidence = 0.7
        elif cv <= 0.55:
            confidence = 0.6
        else:
            confidence = 0.5
        
        return confidence
    
    def _calculate_model_confidence(self, data: Dict[str, Any], pis_score: float) -> float:
        """Calculate confidence based on model-specific factors"""
        # Factors that affect model confidence
        
        # Position-specific confidence
        position = data.get('position', 'MID').upper()
        position_confidence = {
            'GK': 0.8,    # Goalkeepers more predictable
            'DEF': 0.75,  # Defenders moderately predictable
            'MID': 0.7,   # Midfielders less predictable
            'FWD': 0.65   # Forwards least predictable
        }
        
        base_confidence = position_confidence.get(position, 0.7)
        
        # Form-based adjustment
        form = data.get('form', 0.0)
        if form > 7.0:
            form_adjustment = 0.1  # High form = more predictable
        elif form < 3.0:
            form_adjustment = -0.1  # Low form = less predictable
        else:
            form_adjustment = 0.0
        
        # Ownership-based adjustment
        ownership = data.get('selected_by_percent', 50.0)
        if ownership > 30.0:
            ownership_adjustment = 0.05  # Popular players more predictable
        elif ownership < 5.0:
            ownership_adjustment = -0.1  # Unpopular players less predictable
        else:
            ownership_adjustment = 0.0
        
        # Price-based adjustment
        price = data.get('price', 10.0)
        if price < 6.0:
            price_adjustment = 0.05  # Cheap players more predictable
        elif price > 12.0:
            price_adjustment = -0.05  # Expensive players less predictable
        else:
            price_adjustment = 0.0
        
        total_confidence = base_confidence + form_adjustment + ownership_adjustment + price_adjustment
        
        return max(0.0, min(1.0, total_confidence))
    
    def _get_confidence_level(self, confidence: float) -> str:
        """Get confidence level description"""
        if confidence >= self.high_confidence_threshold:
            return "HIGH"
        elif confidence >= self.medium_confidence_threshold:
            return "MEDIUM"
        elif confidence >= self.low_confidence_threshold:
            return "LOW"
        else:
            return "VERY_LOW"
    
    def _calculate_confidence_intervals(self, pis_score: float, confidence: float) -> Dict[str, float]:
        """Calculate confidence intervals for the prediction"""
        # Higher confidence = narrower intervals
        
        # Base interval width (as percentage of score)
        if confidence >= 0.8:
            interval_width = 0.15  # 15% of score
        elif confidence >= 0.6:
            interval_width = 0.25  # 25% of score
        elif confidence >= 0.4:
            interval_width = 0.35  # 35% of score
        else:
            interval_width = 0.5   # 50% of score
        
        # Calculate intervals
        margin = pis_score * interval_width
        
        return {
            'lower_bound': max(0.0, pis_score - margin),
            'upper_bound': min(15.0, pis_score + margin),
            'margin': margin,
            'interval_width_percentage': interval_width * 100
        }
    
    def get_confidence_summary(self, confidence_data: Dict[str, Any]) -> str:
        """Get a human-readable confidence summary"""
        confidence = confidence_data['total_confidence']
        level = confidence_data['confidence_level']
        intervals = confidence_data['confidence_intervals']
        
        summary = f"Confidence: {confidence:.1%} ({level})\n"
        summary += f"Prediction Range: {intervals['lower_bound']:.1f} - {intervals['upper_bound']:.1f}\n"
        summary += f"Margin of Error: ±{intervals['margin']:.1f}"
        
        return summary
    
    def validate_prediction_confidence(self, confidence_data: Dict[str, Any]) -> bool:
        """Validate if prediction confidence is acceptable"""
        confidence = confidence_data['total_confidence']
        
        # Minimum confidence threshold
        min_confidence = self.config.get('min_confidence_threshold', 0.3)
        
        return confidence >= min_confidence 