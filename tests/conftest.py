"""
Pytest configuration and common fixtures.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any

# Configure pytest for async tests
pytest_plugins = ["pytest_asyncio"]


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_database_session():
    """Mock database session for testing."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        "database": {
            "host": "localhost",
            "port": 5432,
            "database": "test_db",
            "username": "test_user",
            "password": "test_pass"
        },
        "scraper": {
            "rate_limit_delay": 1.0,
            "max_retries": 3,
            "request_timeout": 30,
            "requests_per_minute": 60,
            "requests_per_hour": 1000
        },
        "logging": {
            "level": "INFO",
            "format": "json"
        }
    }


@pytest.fixture
def sample_player_data():
    """Sample player data for testing."""
    return {
        "id": 1,
        "name": "Test Player",
        "team": "Test Team",
        "position": "MID",
        "points": 100,
        "price": 8.5,
        "form": 7.5,
        "points_per_game": 6.2,
        "selected_by_percent": 15.2,
        "transfers_in": 5000,
        "transfers_out": 2000,
        "goals_scored": 5,
        "assists": 8,
        "clean_sheets": 10,
        "goals_conceded": 15,
        "yellow_cards": 3,
        "red_cards": 0,
        "bonus": 12,
        "bps": 450,
        "influence": 750.5,
        "creativity": 650.2,
        "threat": 800.1,
        "ict_index": 733.6,
        "starts": 25,
        "expected_goals": 8.5,
        "expected_assists": 6.2,
        "expected_goal_involvements": 14.7,
        "expected_goals_conceded": 18.3
    }


@pytest.fixture
def sample_team_data():
    """Sample team data for testing."""
    return {
        "id": 1,
        "name": "Test Team",
        "short_name": "TST",
        "strength": 4,
        "strength_overall_home": 1200,
        "strength_overall_away": 1100,
        "strength_attack_home": 1200,
        "strength_attack_away": 1100,
        "strength_defence_home": 1200,
        "strength_defence_away": 1100
    }


@pytest.fixture
def sample_scraped_data(sample_player_data, sample_team_data):
    """Sample scraped data for testing."""
    return {
        "players": [sample_player_data],
        "teams": [sample_team_data]
    }


@pytest.fixture
def mock_repository():
    """Mock repository for testing."""
    repo = AsyncMock()
    repo.save_players = AsyncMock(return_value=1)
    repo.save_teams = AsyncMock(return_value=1)
    repo.get_player_by_id = AsyncMock(return_value=None)
    repo.get_team_by_id = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    logger = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.debug = Mock()
    return logger 