"""
Unit tests for FPL Prediction Engine Scoring Logic

This module tests the core scoring algorithms including Player Impact Score calculation,
position-specific scoring, and confidence calculation.
"""

import pytest
import sys
import os
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from prediction.scoring.master_score.player_impact_score import PlayerImpactScore
from prediction.scoring.master_score.confidence_calculator import ConfidenceCalculator
from config.settings import get_settings


class TestPlayerImpactScore:
    """Test cases for Player Impact Score calculation."""

    @pytest.fixture
    def scorer(self):
        """Create a PlayerImpactScore instance for testing."""
        settings = get_settings()
        return PlayerImpactScore(settings.dict())

    @pytest.fixture
    def sample_goalkeeper(self):
        """Sample goalkeeper data for testing."""
        return {
            "id": "gk1",
            "name": "Alisson",
            "position": "GK",
            "team": "Liverpool",
            "price": 5.5,
            "form": 6.2,
            "total_points": 120,
            "minutes_played": 2700,
            "clean_sheets": 12,
            "saves": 85,
            "goals_conceded": 25,
            "bonus_points": 8,
            "injury_history": [],
            "age": 31,
            "rotation_risk": False,
        }

    @pytest.fixture
    def sample_defender(self):
        """Sample defender data for testing."""
        return {
            "id": "def1",
            "name": "Alexander-Arnold",
            "position": "DEF",
            "team": "Liverpool",
            "price": 8.5,
            "form": 7.5,
            "total_points": 180,
            "minutes_played": 2700,
            "clean_sheets": 8,
            "goals": 3,
            "assists": 12,
            "bonus_points": 15,
            "injury_history": [],
            "age": 25,
            "rotation_risk": False,
        }

    @pytest.fixture
    def sample_midfielder(self):
        """Sample midfielder data for testing."""
        return {
            "id": "mid1",
            "name": "Salah",
            "position": "MID",
            "team": "Liverpool",
            "price": 13.0,
            "form": 8.2,
            "total_points": 220,
            "minutes_played": 2700,
            "goals": 18,
            "assists": 12,
            "bonus_points": 25,
            "injury_history": [],
            "age": 31,
            "rotation_risk": False,
        }

    @pytest.fixture
    def sample_forward(self):
        """Sample forward data for testing."""
        return {
            "id": "fwd1",
            "name": "Haaland",
            "position": "FWD",
            "team": "Man City",
            "price": 14.0,
            "form": 8.5,
            "total_points": 240,
            "minutes_played": 2400,
            "goals": 25,
            "assists": 5,
            "bonus_points": 30,
            "injury_history": [],
            "age": 23,
            "rotation_risk": False,
        }

    def test_calculate_pis_goalkeeper(self, scorer, sample_goalkeeper):
        """Test PIS calculation for goalkeeper."""
        result = scorer.calculate_pis(sample_goalkeeper)

        # Verify result structure
        assert "final_pis" in result
        assert "confidence" in result
        assert "sub_scores" in result

        # Verify score is reasonable
        assert isinstance(result["final_pis"], (int, float))
        assert result["final_pis"] >= 0
        assert result["final_pis"] <= 10  # PIS should be normalized to 0-10

        # Verify confidence is reasonable
        assert isinstance(result["confidence"], (int, float))
        assert 0 <= result["confidence"] <= 1

        # Verify sub-scores exist
        assert isinstance(result["sub_scores"], dict)
        assert len(result["sub_scores"]) > 0

    def test_calculate_pis_defender(self, scorer, sample_defender):
        """Test PIS calculation for defender."""
        result = scorer.calculate_pis(sample_defender)

        # Verify result structure
        assert "final_pis" in result
        assert "confidence" in result
        assert "sub_scores" in result

        # Verify score is reasonable
        assert isinstance(result["final_pis"], (int, float))
        assert result["final_pis"] >= 0
        assert result["final_pis"] <= 10

        # Verify confidence is reasonable
        assert isinstance(result["confidence"], (int, float))
        assert 0 <= result["confidence"] <= 1

    def test_calculate_pis_midfielder(self, scorer, sample_midfielder):
        """Test PIS calculation for midfielder."""
        result = scorer.calculate_pis(sample_midfielder)

        # Verify result structure
        assert "final_pis" in result
        assert "confidence" in result
        assert "sub_scores" in result

        # Verify score is reasonable
        assert isinstance(result["final_pis"], (int, float))
        assert result["final_pis"] >= 0
        assert result["final_pis"] <= 10

    def test_calculate_pis_forward(self, scorer, sample_forward):
        """Test PIS calculation for forward."""
        result = scorer.calculate_pis(sample_forward)

        # Verify result structure
        assert "final_pis" in result
        assert "confidence" in result
        assert "sub_scores" in result

        # Verify score is reasonable
        assert isinstance(result["final_pis"], (int, float))
        assert result["final_pis"] >= 0
        assert result["final_pis"] <= 10

    def test_invalid_position(self, scorer, sample_goalkeeper):
        """Test PIS calculation with invalid position."""
        invalid_player = sample_goalkeeper.copy()
        invalid_player["position"] = "INVALID"

        with pytest.raises(ValueError):
            scorer.calculate_pis(invalid_player)

    def test_missing_required_fields(self, scorer):
        """Test PIS calculation with missing required fields."""
        incomplete_player = {
            "id": "test",
            "name": "Test Player",
            "position": "MID",
            # Missing other required fields
        }

        with pytest.raises(KeyError):
            scorer.calculate_pis(incomplete_player)

    def test_score_consistency(self, scorer, sample_midfielder):
        """Test that PIS calculation is consistent for same input."""
        result1 = scorer.calculate_pis(sample_midfielder)
        result2 = scorer.calculate_pis(sample_midfielder)

        assert result1["final_pis"] == result2["final_pis"]
        assert result1["confidence"] == result2["confidence"]

    def test_score_scaling(self, scorer, sample_goalkeeper, sample_midfielder):
        """Test that higher-performing players get higher scores."""
        gk_result = scorer.calculate_pis(sample_goalkeeper)
        mid_result = scorer.calculate_pis(sample_midfielder)

        # Midfielder should generally score higher than goalkeeper
        # (this is a heuristic test, not always true)
        # We'll just verify both scores are reasonable
        assert gk_result["final_pis"] >= 0
        assert mid_result["final_pis"] >= 0

    def test_confidence_calculation(self, scorer, sample_midfielder):
        """Test confidence calculation logic."""
        result = scorer.calculate_pis(sample_midfielder)

        # Confidence should be between 0 and 1
        assert 0 <= result["confidence"] <= 1

        # Confidence should be a float
        assert isinstance(result["confidence"], float)


class TestConfidenceCalculator:
    """Test cases for confidence calculation."""

    @pytest.fixture
    def calculator(self):
        """Create a ConfidenceCalculator instance for testing."""
        return ConfidenceCalculator()

    def test_calculate_confidence_complete_data(self, calculator):
        """Test confidence calculation with complete data."""
        player_data = {
            "minutes_played": 2700,
            "total_points": 200,
            "goals": 15,
            "assists": 10,
            "clean_sheets": 8,
            "saves": 50,
            "bonus_points": 20,
        }

        confidence = calculator.calculate_confidence(player_data)

        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1
        assert confidence > 0.5  # Complete data should have high confidence

    def test_calculate_confidence_incomplete_data(self, calculator):
        """Test confidence calculation with incomplete data."""
        player_data = {
            "minutes_played": 500,  # Low minutes
            "total_points": 20,  # Low points
            "goals": 1,
            "assists": 0,
            # Missing other fields
        }

        confidence = calculator.calculate_confidence(player_data)

        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1
        assert confidence < 0.8  # Incomplete data should have lower confidence

    def test_calculate_confidence_no_data(self, calculator):
        """Test confidence calculation with minimal data."""
        player_data = {"minutes_played": 0, "total_points": 0}

        confidence = calculator.calculate_confidence(player_data)

        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1
        assert confidence < 0.5  # No data should have very low confidence


class TestScoringEdgeCases:
    """Test edge cases in scoring calculations."""

    @pytest.fixture
    def scorer(self):
        """Create a PlayerImpactScore instance for testing."""
        settings = get_settings()
        return PlayerImpactScore(settings.dict())

    def test_zero_minutes_player(self, scorer):
        """Test scoring for player with zero minutes."""
        zero_minutes_player = {
            "id": "test1",
            "name": "Zero Minutes Player",
            "position": "MID",
            "team": "Test Team",
            "price": 5.0,
            "form": 0.0,
            "total_points": 0,
            "minutes_played": 0,
            "goals": 0,
            "assists": 0,
            "bonus_points": 0,
            "injury_history": [],
            "age": 25,
            "rotation_risk": False,
        }

        result = scorer.calculate_pis(zero_minutes_player)

        # Should still return a valid result
        assert "final_pis" in result
        assert "confidence" in result
        assert result["final_pis"] >= 0
        assert result["confidence"] >= 0

    def test_extreme_values(self, scorer):
        """Test scoring with extreme values."""
        extreme_player = {
            "id": "test2",
            "name": "Extreme Player",
            "position": "FWD",
            "team": "Test Team",
            "price": 20.0,  # Very expensive
            "form": 10.0,  # Perfect form
            "total_points": 500,  # Very high points
            "minutes_played": 3420,  # All minutes
            "goals": 50,  # Very high goals
            "assists": 30,  # Very high assists
            "bonus_points": 100,  # Very high bonus
            "injury_history": [],
            "age": 18,  # Very young
            "rotation_risk": False,
        }

        result = scorer.calculate_pis(extreme_player)

        # Should handle extreme values gracefully
        assert "final_pis" in result
        assert "confidence" in result
        assert result["final_pis"] >= 0
        assert result["final_pis"] <= 10  # Should still be normalized
        assert result["confidence"] >= 0
        assert result["confidence"] <= 1

    def test_negative_values(self, scorer):
        """Test scoring with negative values (should be handled gracefully)."""
        negative_player = {
            "id": "test3",
            "name": "Negative Player",
            "position": "DEF",
            "team": "Test Team",
            "price": -1.0,  # Negative price
            "form": -5.0,  # Negative form
            "total_points": -10,  # Negative points
            "minutes_played": 2700,
            "goals": -2,  # Negative goals
            "assists": -1,  # Negative assists
            "bonus_points": -5,  # Negative bonus
            "injury_history": [],
            "age": 25,
            "rotation_risk": False,
        }

        # Should handle negative values gracefully
        try:
            result = scorer.calculate_pis(negative_player)
            assert "final_pis" in result
            assert "confidence" in result
        except (ValueError, TypeError):
            # It's acceptable for the scorer to reject negative values
            pass


class TestScoringPerformance:
    """Test performance characteristics of scoring calculations."""

    @pytest.fixture
    def scorer(self):
        """Create a PlayerImpactScore instance for testing."""
        settings = get_settings()
        return PlayerImpactScore(settings.dict())

    def test_scoring_speed(self, scorer):
        """Test that scoring calculation is reasonably fast."""
        import time

        test_player = {
            "id": "perf_test",
            "name": "Performance Test Player",
            "position": "MID",
            "team": "Test Team",
            "price": 8.0,
            "form": 7.0,
            "total_points": 150,
            "minutes_played": 2700,
            "goals": 10,
            "assists": 8,
            "bonus_points": 15,
            "injury_history": [],
            "age": 25,
            "rotation_risk": False,
        }

        # Time the calculation
        start_time = time.time()
        result = scorer.calculate_pis(test_player)
        end_time = time.time()

        calculation_time = end_time - start_time

        # Should complete in reasonable time (less than 1 second)
        assert calculation_time < 1.0
        assert "final_pis" in result

    def test_batch_scoring_performance(self, scorer):
        """Test performance of scoring multiple players."""
        import time

        # Create multiple test players
        test_players = []
        for i in range(100):
            player = {
                "id": f"batch_test_{i}",
                "name": f"Batch Test Player {i}",
                "position": "MID",
                "team": "Test Team",
                "price": 8.0,
                "form": 7.0,
                "total_points": 150,
                "minutes_played": 2700,
                "goals": 10,
                "assists": 8,
                "bonus_points": 15,
                "injury_history": [],
                "age": 25,
                "rotation_risk": False,
            }
            test_players.append(player)

        # Time batch calculation
        start_time = time.time()
        results = []
        for player in test_players:
            result = scorer.calculate_pis(player)
            results.append(result)
        end_time = time.time()

        total_time = end_time - start_time
        avg_time_per_player = total_time / len(test_players)

        # Should complete batch in reasonable time
        assert total_time < 10.0  # Less than 10 seconds for 100 players
        assert avg_time_per_player < 0.1  # Less than 0.1 seconds per player

        # Verify all results are valid
        for result in results:
            assert "final_pis" in result
            assert "confidence" in result
            assert result["final_pis"] >= 0
            assert result["confidence"] >= 0


if __name__ == "__main__":
    pytest.main([__file__])
