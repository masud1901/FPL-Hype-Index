"""
Validation Module

This module contains backtesting and validation logic for the prediction engine.
Provides tools to evaluate model performance and generate performance reports.
"""

from .backtesting.backtest_engine import BacktestEngine
from .metrics.performance_metrics import PerformanceMetrics

__all__ = ["BacktestEngine", "PerformanceMetrics"] 