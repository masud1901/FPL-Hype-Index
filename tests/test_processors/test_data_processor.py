"""
Unit tests for DataProcessor.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import Dict, Any

from processors.data_processor import DataProcessor
from processors.data_cleaner import DataCleaner
from processors.data_validator import DataValidator
from processors.data_enricher import DataEnricher


class TestDataProcessor:
    """Test cases for DataProcessor class."""
    
    @pytest.fixture
    def mock_cleaner(self):
        """Mock DataCleaner instance."""
        cleaner = Mock(spec=DataCleaner)
        cleaner.clean_data.return_value = {
            "players": [
                {"id": 1, "name": "Test Player", "team": "Test Team", "position": "MID"}
            ]
        }
        return cleaner
    
    @pytest.fixture
    def mock_validator(self):
        """Mock DataValidator instance."""
        validator = Mock(spec=DataValidator)
        validator.validate_data.return_value = True
        validator.get_validation_errors.return_value = []
        return validator
    
    @pytest.fixture
    def mock_enricher(self):
        """Mock DataEnricher instance."""
        enricher = Mock(spec=DataEnricher)
        enricher.enrich_data.return_value = {
            "players": [
                {
                    "id": 1, 
                    "name": "Test Player", 
                    "team": "Test Team", 
                    "position": "MID",
                    "form_score": 7.5,
                    "fixture_difficulty": 2
                }
            ]
        }
        return enricher
    
    @pytest.fixture
    def sample_scraped_data(self):
        """Sample scraped data for testing."""
        return {
            "players": [
                {
                    "id": 1,
                    "name": "Test Player",
                    "team": "Test Team",
                    "position": "MID",
                    "points": 100,
                    "price": 8.5
                }
            ],
            "teams": [
                {
                    "id": 1,
                    "name": "Test Team",
                    "short_name": "TST"
                }
            ]
        }
    
    @pytest.fixture
    def processor(self, mock_cleaner, mock_validator, mock_enricher):
        """DataProcessor instance with mocked dependencies."""
        return DataProcessor(
            cleaner=mock_cleaner,
            validator=mock_validator,
            enricher=mock_enricher
        )
    
    def test_processor_initialization(self, processor):
        """Test DataProcessor initialization."""
        assert processor.cleaner is not None
        assert processor.validator is not None
        assert processor.enricher is not None
    
    @pytest.mark.asyncio
    async def test_process_scraped_data_success(self, processor, sample_scraped_data):
        """Test successful data processing flow."""
        # Mock repository
        mock_repository = AsyncMock()
        mock_repository.save_players.return_value = 1
        mock_repository.save_teams.return_value = 1
        
        result = await processor.process_scraped_data(
            sample_scraped_data, 
            "test_scraper", 
            mock_repository
        )
        
        # Verify the processing flow
        processor.cleaner.clean_data.assert_called_once_with(sample_scraped_data)
        processor.validator.validate_data.assert_called_once()
        processor.enricher.enrich_data.assert_called_once()
        mock_repository.save_players.assert_called_once()
        mock_repository.save_teams.assert_called_once()
        
        assert result["status"] == "success"
        assert result["players_processed"] == 1
        assert result["teams_processed"] == 1
    
    @pytest.mark.asyncio
    async def test_process_scraped_data_validation_failure(self, processor, sample_scraped_data):
        """Test data processing with validation failure."""
        # Mock validator to fail
        processor.validator.validate_data.return_value = False
        processor.validator.get_validation_errors.return_value = ["Invalid data format"]
        
        # Mock repository
        mock_repository = AsyncMock()
        
        result = await processor.process_scraped_data(
            sample_scraped_data, 
            "test_scraper", 
            mock_repository
        )
        
        assert result["status"] == "error"
        assert "validation" in result["error"].lower()
        assert "Invalid data format" in result["error"]
        
        # Verify enricher and repository were not called
        processor.enricher.enrich_data.assert_not_called()
        mock_repository.save_players.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_scraped_data_cleaning_failure(self, processor, sample_scraped_data):
        """Test data processing with cleaning failure."""
        # Mock cleaner to raise exception
        processor.cleaner.clean_data.side_effect = Exception("Cleaning failed")
        
        # Mock repository
        mock_repository = AsyncMock()
        
        result = await processor.process_scraped_data(
            sample_scraped_data, 
            "test_scraper", 
            mock_repository
        )
        
        assert result["status"] == "error"
        assert "cleaning" in result["error"].lower()
        
        # Verify subsequent steps were not called
        processor.validator.validate_data.assert_not_called()
        processor.enricher.enrich_data.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_scraped_data_enrichment_failure(self, processor, sample_scraped_data):
        """Test data processing with enrichment failure."""
        # Mock enricher to raise exception
        processor.enricher.enrich_data.side_effect = Exception("Enrichment failed")
        
        # Mock repository
        mock_repository = AsyncMock()
        
        result = await processor.process_scraped_data(
            sample_scraped_data, 
            "test_scraper", 
            mock_repository
        )
        
        assert result["status"] == "error"
        assert "enrichment" in result["error"].lower()
        
        # Verify repository was not called
        mock_repository.save_players.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_scraped_data_save_failure(self, processor, sample_scraped_data):
        """Test data processing with save failure."""
        # Mock repository to raise exception
        mock_repository = AsyncMock()
        mock_repository.save_players.side_effect = Exception("Database error")
        
        result = await processor.process_scraped_data(
            sample_scraped_data, 
            "test_scraper", 
            mock_repository
        )
        
        assert result["status"] == "error"
        assert "save" in result["error"].lower()
    
    def test_processor_with_default_dependencies(self):
        """Test DataProcessor initialization with default dependencies."""
        processor = DataProcessor()
        
        assert processor.cleaner is not None
        assert processor.validator is not None
        assert processor.enricher is not None
        assert isinstance(processor.cleaner, DataCleaner)
        assert isinstance(processor.validator, DataValidator)
        assert isinstance(processor.enricher, DataEnricher)


class TestDataCleaner:
    """Test cases for DataCleaner class."""
    
    @pytest.fixture
    def cleaner(self):
        """DataCleaner instance."""
        return DataCleaner()
    
    def test_clean_data_basic(self, cleaner):
        """Test basic data cleaning."""
        raw_data = {
            "players": [
                {
                    "id": 1,
                    "name": "  Test Player  ",  # Extra whitespace
                    "team": "Test Team",
                    "position": "mid",  # Lowercase
                    "points": "100",  # String instead of int
                    "price": 8.5
                }
            ]
        }
        
        cleaned_data = cleaner.clean_data(raw_data)
        
        assert cleaned_data["players"][0]["name"] == "Test Player"
        assert cleaned_data["players"][0]["position"] == "MID"
        assert cleaned_data["players"][0]["points"] == 100
        assert cleaned_data["players"][0]["price"] == 8.5
    
    def test_clean_data_missing_fields(self, cleaner):
        """Test data cleaning with missing fields."""
        raw_data = {
            "players": [
                {
                    "id": 1,
                    "name": "Test Player",
                    # Missing team, position, points, price
                }
            ]
        }
        
        cleaned_data = cleaner.clean_data(raw_data)
        
        # Should add default values for missing fields
        assert cleaned_data["players"][0]["team"] == "Unknown"
        assert cleaned_data["players"][0]["position"] == "UNK"
        assert cleaned_data["players"][0]["points"] == 0
        assert cleaned_data["players"][0]["price"] == 0.0
    
    def test_clean_data_empty_input(self, cleaner):
        """Test data cleaning with empty input."""
        raw_data = {}
        
        cleaned_data = cleaner.clean_data(raw_data)
        
        assert cleaned_data == {"players": [], "teams": []}


class TestDataValidator:
    """Test cases for DataValidator class."""
    
    @pytest.fixture
    def validator(self):
        """DataValidator instance."""
        return DataValidator()
    
    def test_validate_data_valid(self, validator):
        """Test validation with valid data."""
        data = {
            "players": [
                {
                    "id": 1,
                    "name": "Test Player",
                    "team": "Test Team",
                    "position": "MID",
                    "points": 100,
                    "price": 8.5
                }
            ]
        }
        
        assert validator.validate_data(data) is True
        assert validator.get_validation_errors() == []
    
    def test_validate_data_invalid_player(self, validator):
        """Test validation with invalid player data."""
        data = {
            "players": [
                {
                    "id": "invalid",  # Should be int
                    "name": "",  # Empty name
                    "team": "Test Team",
                    "position": "INVALID",  # Invalid position
                    "points": -1,  # Negative points
                    "price": -5.0  # Negative price
                }
            ]
        }
        
        assert validator.validate_data(data) is False
        errors = validator.get_validation_errors()
        assert len(errors) > 0
        assert any("id" in error.lower() for error in errors)
        assert any("name" in error.lower() for error in errors)
        assert any("position" in error.lower() for error in errors)
    
    def test_validate_data_missing_required_fields(self, validator):
        """Test validation with missing required fields."""
        data = {
            "players": [
                {
                    "name": "Test Player"
                    # Missing id, team, position, etc.
                }
            ]
        }
        
        assert validator.validate_data(data) is False
        errors = validator.get_validation_errors()
        assert len(errors) > 0
        assert any("required" in error.lower() for error in errors)


class TestDataEnricher:
    """Test cases for DataEnricher class."""
    
    @pytest.fixture
    def enricher(self):
        """DataEnricher instance."""
        return DataEnricher()
    
    def test_enrich_data_basic(self, enricher):
        """Test basic data enrichment."""
        data = {
            "players": [
                {
                    "id": 1,
                    "name": "Test Player",
                    "team": "Test Team",
                    "position": "MID",
                    "points": 100,
                    "price": 8.5
                }
            ]
        }
        
        enriched_data = enricher.enrich_data(data)
        
        # Should add enrichment fields
        player = enriched_data["players"][0]
        assert "form_score" in player
        assert "fixture_difficulty" in player
        assert "value_score" in player
        assert isinstance(player["form_score"], (int, float))
        assert isinstance(player["fixture_difficulty"], (int, float))
        assert isinstance(player["value_score"], (int, float))
    
    def test_enrich_data_empty_input(self, enricher):
        """Test data enrichment with empty input."""
        data = {"players": []}
        
        enriched_data = enricher.enrich_data(data)
        
        assert enriched_data["players"] == []
    
    def test_enrich_data_with_existing_enrichment(self, enricher):
        """Test data enrichment with existing enrichment fields."""
        data = {
            "players": [
                {
                    "id": 1,
                    "name": "Test Player",
                    "team": "Test Team",
                    "position": "MID",
                    "points": 100,
                    "price": 8.5,
                    "form_score": 8.0  # Already enriched
                }
            ]
        }
        
        enriched_data = enricher.enrich_data(data)
        
        # Should preserve existing enrichment and add missing ones
        player = enriched_data["players"][0]
        assert player["form_score"] == 8.0  # Preserved
        assert "fixture_difficulty" in player  # Added
        assert "value_score" in player  # Added 