#!/usr/bin/env python3
"""
Comprehensive test script for the FPL Prediction Engine.

This script tests all major components:
1. Player Impact Score calculation
2. Transfer optimization
3. Backtesting engine
4. API endpoints
5. Caching functionality
6. Performance metrics
"""

import sys
import os
import time
import json
import requests
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from prediction.scoring.master_score.player_impact_score import PlayerImpactScore
from prediction.optimization.algorithms.transfer_optimizer import TransferOptimizer
from prediction.validation.backtesting.backtest_engine import BacktestEngine
from prediction.validation.backtesting.performance_metrics import PerformanceMetrics
from utils.cache import get_cache, cache_player_score, get_cached_player_score
from config.settings import get_settings
from scripts.run_prediction_optimization import create_sample_squad, create_available_players


class PredictionEngineTester:
    """Comprehensive tester for the FPL Prediction Engine."""
    
    def __init__(self):
        """Initialize the tester."""
        self.settings = get_settings()
        self.results = {}
        self.api_base_url = "http://localhost:8000/api/v1"
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return results."""
        print("🚀 Starting FPL Prediction Engine Comprehensive Tests")
        print("=" * 80)
        
        test_functions = [
            ("Player Impact Score", self.test_player_impact_score),
            ("Transfer Optimization", self.test_transfer_optimization),
            ("Backtesting Engine", self.test_backtesting_engine),
            ("Performance Metrics", self.test_performance_metrics),
            ("Caching System", self.test_caching_system),
            ("API Endpoints", self.test_api_endpoints),
            ("Integration Tests", self.test_integration),
        ]
        
        for test_name, test_func in test_functions:
            print(f"\n📋 Running {test_name} Tests...")
            try:
                start_time = time.time()
                result = test_func()
                end_time = time.time()
                
                self.results[test_name] = {
                    "status": "PASSED" if result else "FAILED",
                    "duration": end_time - start_time,
                    "details": result
                }
                
                status_emoji = "✅" if result else "❌"
                print(f"{status_emoji} {test_name}: {'PASSED' if result else 'FAILED'} ({end_time - start_time:.2f}s)")
                
            except Exception as e:
                self.results[test_name] = {
                    "status": "ERROR",
                    "duration": 0,
                    "error": str(e)
                }
                print(f"❌ {test_name}: ERROR - {e}")
        
        return self.results
    
    def test_player_impact_score(self) -> bool:
        """Test Player Impact Score calculation."""
        try:
            scorer = PlayerImpactScore(self.settings.dict())
            
            # Test with sample players
            sample_squad = create_sample_squad()
            
            for player in sample_squad[:5]:  # Test first 5 players
                result = scorer.calculate_pis(player)
                
                # Verify result structure
                assert "final_pis" in result
                assert "confidence" in result
                assert "sub_scores" in result
                
                # Verify score ranges
                assert 0 <= result["final_pis"] <= 10
                assert 0 <= result["confidence"] <= 1
                
                print(f"  ✓ {player['name']}: PIS={result['final_pis']:.2f}, Confidence={result['confidence']:.2f}")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Player Impact Score test failed: {e}")
            return False
    
    def test_transfer_optimization(self) -> bool:
        """Test transfer optimization functionality."""
        try:
            optimizer = TransferOptimizer(self.settings.dict())
            current_squad = create_sample_squad()
            available_players = create_available_players()
            
            # Test single transfer recommendations
            single_recs = optimizer.get_single_transfer_recommendations(
                current_squad=current_squad,
                available_players=available_players,
                budget=2.0
            )
            
            assert len(single_recs) > 0
            print(f"  ✓ Generated {len(single_recs)} single transfer recommendations")
            
            # Test transfer combinations
            combinations = optimizer.optimize_transfers(
                current_squad=current_squad,
                available_players=available_players,
                budget=2.0,
                transfers_available=2,
                strategy="balanced"
            )
            
            assert len(combinations) > 0
            print(f"  ✓ Generated {len(combinations)} transfer combinations")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Transfer optimization test failed: {e}")
            return False
    
    def test_backtesting_engine(self) -> bool:
        """Test backtesting engine functionality."""
        try:
            engine = BacktestEngine(self.settings.dict())
            initial_squad = create_sample_squad()
            
            # Run a short backtest
            result = engine.run_backtest(
                start_gameweek=1,
                end_gameweek=5,
                initial_squad=initial_squad
            )
            
            # Verify result structure
            assert result.total_points >= 0
            assert result.average_points_per_gameweek >= 0
            assert len(result.gameweek_results) == 5
            
            print(f"  ✓ Backtest completed: {result.total_points:.1f} total points")
            print(f"  ✓ Average: {result.average_points_per_gameweek:.1f} points per gameweek")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Backtesting engine test failed: {e}")
            return False
    
    def test_performance_metrics(self) -> bool:
        """Test performance metrics calculation."""
        try:
            metrics_calc = PerformanceMetrics()
            
            # Create sample data
            predicted_scores = [7.5, 6.8, 8.2, 5.9, 7.1, 6.3, 8.5, 6.7, 7.8, 6.1]
            actual_points = [8, 7, 9, 6, 7, 6, 8, 7, 8, 6]
            
            # Calculate metrics
            metrics = metrics_calc.calculate_all_metrics(predicted_scores, actual_points)
            
            # Verify key metrics exist
            assert "pearson_correlation" in metrics
            assert "spearman_correlation" in metrics
            assert "mean_absolute_error" in metrics
            assert "r_squared" in metrics
            
            print(f"  ✓ Calculated {len(metrics)} performance metrics")
            print(f"  ✓ Pearson correlation: {metrics['pearson_correlation']:.3f}")
            print(f"  ✓ R-squared: {metrics['r_squared']:.3f}")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Performance metrics test failed: {e}")
            return False
    
    def test_caching_system(self) -> bool:
        """Test Redis caching functionality."""
        try:
            cache = get_cache()
            
            # Test basic cache operations
            test_key = "test_player_score"
            test_data = {"player_id": "test123", "score": 7.5, "confidence": 0.8}
            
            # Test set and get
            success = cache.set(test_key, test_data, ttl=60)
            assert success
            
            retrieved_data = cache.get(test_key)
            assert retrieved_data == test_data
            
            # Test player score caching
            cache_player_score("test123", test_data)
            cached_score = get_cached_player_score("test123")
            assert cached_score == test_data
            
            print("  ✓ Basic cache operations working")
            print("  ✓ Player score caching working")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Caching system test failed: {e}")
            return False
    
    def test_api_endpoints(self) -> bool:
        """Test API endpoints."""
        try:
            # Test health endpoint
            health_response = requests.get(f"{self.api_base_url}/health", timeout=10)
            assert health_response.status_code == 200
            
            # Test prediction health endpoint
            pred_health_response = requests.get(f"{self.api_base_url}/prediction/health", timeout=10)
            assert pred_health_response.status_code == 200
            
            # Test strategies endpoint
            strategies_response = requests.get(f"{self.api_base_url}/prediction/strategies", timeout=10)
            assert strategies_response.status_code == 200
            
            strategies = strategies_response.json()
            assert "balanced" in strategies
            assert "aggressive" in strategies
            assert "conservative" in strategies
            
            print("  ✓ Health endpoints working")
            print("  ✓ Strategies endpoint working")
            
            return True
            
        except Exception as e:
            print(f"  ❌ API endpoints test failed: {e}")
            return False
    
    def test_integration(self) -> bool:
        """Test integration between components."""
        try:
            # Test full workflow: score players -> optimize transfers -> backtest
            scorer = PlayerImpactScore(self.settings.dict())
            optimizer = TransferOptimizer(self.settings.dict())
            engine = BacktestEngine(self.settings.dict())
            
            # Create sample data
            current_squad = create_sample_squad()
            available_players = create_available_players()
            
            # Score current squad
            squad_scores = []
            for player in current_squad:
                score_result = scorer.calculate_pis(player)
                squad_scores.append(score_result["final_pis"])
            
            # Get transfer recommendations
            recommendations = optimizer.get_single_transfer_recommendations(
                current_squad=current_squad,
                available_players=available_players,
                budget=2.0
            )
            
            # Run backtest with current squad
            backtest_result = engine.run_backtest(
                start_gameweek=1,
                end_gameweek=3,
                initial_squad=current_squad
            )
            
            print(f"  ✓ Integration test completed successfully")
            print(f"  ✓ Squad average score: {sum(squad_scores)/len(squad_scores):.2f}")
            print(f"  ✓ Transfer recommendations: {len(recommendations)}")
            print(f"  ✓ Backtest points: {backtest_result.total_points:.1f}")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Integration test failed: {e}")
            return False
    
    def generate_report(self) -> str:
        """Generate a comprehensive test report."""
        report = []
        report.append("FPL PREDICTION ENGINE TEST REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results.values() if r["status"] == "PASSED")
        failed_tests = sum(1 for r in self.results.values() if r["status"] == "FAILED")
        error_tests = sum(1 for r in self.results.values() if r["status"] == "ERROR")
        
        report.append("SUMMARY")
        report.append("-" * 40)
        report.append(f"Total Tests: {total_tests}")
        report.append(f"Passed: {passed_tests}")
        report.append(f"Failed: {failed_tests}")
        report.append(f"Errors: {error_tests}")
        report.append(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        report.append("")
        
        # Detailed results
        report.append("DETAILED RESULTS")
        report.append("-" * 40)
        
        for test_name, result in self.results.items():
            status_emoji = "✅" if result["status"] == "PASSED" else "❌" if result["status"] == "FAILED" else "⚠️"
            report.append(f"{status_emoji} {test_name}: {result['status']} ({result['duration']:.2f}s)")
            
            if result["status"] == "ERROR":
                report.append(f"    Error: {result['error']}")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)


def main():
    """Main execution function."""
    print("🧪 FPL Prediction Engine Comprehensive Testing")
    print("=" * 80)
    
    # Create tester
    tester = PredictionEngineTester()
    
    # Run all tests
    results = tester.run_all_tests()
    
    # Generate and display report
    report = tester.generate_report()
    print("\n" + report)
    
    # Save report to file
    with open("logs/test_report.txt", "w") as f:
        f.write(report)
    
    # Determine overall success
    passed_tests = sum(1 for r in results.values() if r["status"] == "PASSED")
    total_tests = len(results)
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed! The FPL Prediction Engine is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total_tests - passed_tests} tests failed. Please check the report above.")
        return 1


if __name__ == "__main__":
    exit(main()) 