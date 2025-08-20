"""
Unit tests for FPL API scraper.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import Dict, Any

from scrapers.fpl_api.fpl_scraper import FPLScraper
from scrapers.fpl_api.models import FPLPlayer, FPLTeam


class TestFPLScraper:
    """Test cases for FPLScraper class."""
    
    @pytest.fixture
    def scraper(self):
        """FPLScraper instance."""
        return FPLScraper()
    
    @pytest.fixture
    def mock_fpl_data(self):
        """Mock FPL API response data."""
        return {
            "elements": [
                {
                    "id": 1,
                    "first_name": "Test",
                    "second_name": "Player",
                    "web_name": "T. Player",
                    "team": 1,
                    "element_type": 3,  # MID
                    "total_points": 100,
                    "now_cost": 85,  # 8.5 in FPL format
                    "form": "7.5",
                    "points_per_game": "6.2",
                    "selected_by_percent": "15.2",
                    "transfers_in_event": 5000,
                    "transfers_out_event": 2000,
                    "goals_scored": 5,
                    "assists": 8,
                    "clean_sheets": 10,
                    "goals_conceded": 15,
                    "own_goals": 0,
                    "penalties_saved": 0,
                    "penalties_missed": 0,
                    "yellow_cards": 3,
                    "red_cards": 0,
                    "saves": 0,
                    "bonus": 12,
                    "bps": 450,
                    "influence": "750.5",
                    "creativity": "650.2",
                    "threat": "800.1",
                    "ict_index": "733.6",
                    "starts": 25,
                    "expected_goals": "8.5",
                    "expected_assists": "6.2",
                    "expected_goal_involvements": "14.7",
                    "expected_goals_conceded": "18.3",
                    "influence_rank": 50,
                    "influence_rank_type": 5,
                    "creativity_rank": 45,
                    "creativity_rank_type": 5,
                    "threat_rank": 40,
                    "threat_rank_type": 5,
                    "ict_index_rank": 42,
                    "ict_index_rank_type": 5,
                    "corners_and_indirect_freekicks_order": 1,
                    "corners_and_indirect_freekicks_text": "Takes some",
                    "direct_freekicks_order": 2,
                    "direct_freekicks_text": "Takes some",
                    "penalties_order": 3,
                    "penalties_text": "Takes some"
                }
            ],
            "teams": [
                {
                    "id": 1,
                    "name": "Test Team",
                    "short_name": "TST",
                    "strength": 4,
                    "strength_overall_home": 1200,
                    "strength_overall_away": 1100,
                    "strength_attack_home": 1200,
                    "strength_attack_away": 1100,
                    "strength_defence_home": 1200,
                    "strength_defence_away": 1100,
                    "pulse_id": 1
                }
            ],
            "element_types": [
                {
                    "id": 1,
                    "plural_name": "Goalkeepers",
                    "plural_name_short": "GKP",
                    "singular_name": "Goalkeeper",
                    "singular_name_short": "GKP",
                    "squad_select": 2,
                    "squad_min_play": 0,
                    "squad_max_play": 2,
                    "ui_shirt_specific": True,
                    "sub_positions_locked": [1],
                    "element_count": 20
                },
                {
                    "id": 2,
                    "plural_name": "Defenders",
                    "plural_name_short": "DEF",
                    "singular_name": "Defender",
                    "singular_name_short": "DEF",
                    "squad_select": 5,
                    "squad_min_play": 3,
                    "squad_max_play": 5,
                    "ui_shirt_specific": True,
                    "sub_positions_locked": [2],
                    "element_count": 60
                },
                {
                    "id": 3,
                    "plural_name": "Midfielders",
                    "plural_name_short": "MID",
                    "singular_name": "Midfielder",
                    "singular_name_short": "MID",
                    "squad_select": 5,
                    "squad_min_play": 3,
                    "squad_max_play": 5,
                    "ui_shirt_specific": True,
                    "sub_positions_locked": [3],
                    "element_count": 60
                },
                {
                    "id": 4,
                    "plural_name": "Forwards",
                    "plural_name_short": "FWD",
                    "singular_name": "Forward",
                    "singular_name_short": "FWD",
                    "squad_select": 3,
                    "squad_min_play": 1,
                    "squad_max_play": 3,
                    "ui_shirt_specific": True,
                    "sub_positions_locked": [4],
                    "element_count": 40
                }
            ]
        }
    
    def test_scraper_initialization(self, scraper):
        """Test FPLScraper initialization."""
        assert scraper.name == "fpl"
        assert scraper.base_url == "https://fantasy.premierleague.com/api"
        assert scraper.config is not None
    
    @pytest.mark.asyncio
    async def test_scrape_success(self, scraper, mock_fpl_data):
        """Test successful scraping."""
        with patch.object(scraper, '_make_request') as mock_request:
            mock_request.return_value = mock_fpl_data
            
            result = await scraper.scrape()
            
            # Verify API calls
            assert mock_request.call_count == 1
            mock_request.assert_called_with(f"{scraper.base_url}/bootstrap-static/")
            
            # Verify result structure
            assert "players" in result
            assert "teams" in result
            assert len(result["players"]) == 1
            assert len(result["teams"]) == 1
            
            # Verify player data
            player = result["players"][0]
            assert player["id"] == 1
            assert player["name"] == "Test Player"
            assert player["team"] == "Test Team"
            assert player["position"] == "MID"
            assert player["points"] == 100
            assert player["price"] == 8.5
            assert player["form"] == 7.5
            assert player["selected_by_percent"] == 15.2
            
            # Verify team data
            team = result["teams"][0]
            assert team["id"] == 1
            assert team["name"] == "Test Team"
            assert team["short_name"] == "TST"
    
    @pytest.mark.asyncio
    async def test_scrape_api_error(self, scraper):
        """Test scraping with API error."""
        with patch.object(scraper, '_make_request') as mock_request:
            mock_request.side_effect = Exception("API Error")
            
            with pytest.raises(Exception):
                await scraper.scrape()
    
    def test_parse_players(self, scraper, mock_fpl_data):
        """Test player data parsing."""
        players = scraper._parse_players(mock_fpl_data["elements"], mock_fpl_data["teams"], mock_fpl_data["element_types"])
        
        assert len(players) == 1
        
        player = players[0]
        assert player["id"] == 1
        assert player["name"] == "Test Player"
        assert player["team"] == "Test Team"
        assert player["position"] == "MID"
        assert player["points"] == 100
        assert player["price"] == 8.5
        assert player["form"] == 7.5
        assert player["points_per_game"] == 6.2
        assert player["selected_by_percent"] == 15.2
        assert player["transfers_in"] == 5000
        assert player["transfers_out"] == 2000
        assert player["goals_scored"] == 5
        assert player["assists"] == 8
        assert player["clean_sheets"] == 10
        assert player["goals_conceded"] == 15
        assert player["yellow_cards"] == 3
        assert player["red_cards"] == 0
        assert player["bonus"] == 12
        assert player["bps"] == 450
        assert player["influence"] == 750.5
        assert player["creativity"] == 650.2
        assert player["threat"] == 800.1
        assert player["ict_index"] == 733.6
        assert player["starts"] == 25
        assert player["expected_goals"] == 8.5
        assert player["expected_assists"] == 6.2
        assert player["expected_goal_involvements"] == 14.7
        assert player["expected_goals_conceded"] == 18.3
    
    def test_parse_teams(self, scraper, mock_fpl_data):
        """Test team data parsing."""
        teams = scraper._parse_teams(mock_fpl_data["teams"])
        
        assert len(teams) == 1
        
        team = teams[0]
        assert team["id"] == 1
        assert team["name"] == "Test Team"
        assert team["short_name"] == "TST"
        assert team["strength"] == 4
        assert team["strength_overall_home"] == 1200
        assert team["strength_overall_away"] == 1100
        assert team["strength_attack_home"] == 1200
        assert team["strength_attack_away"] == 1100
        assert team["strength_defence_home"] == 1200
        assert team["strength_defence_away"] == 1100
    
    def test_get_position_name(self, scraper, mock_fpl_data):
        """Test position name mapping."""
        element_types = mock_fpl_data["element_types"]
        
        assert scraper._get_position_name(1, element_types) == "GKP"
        assert scraper._get_position_name(2, element_types) == "DEF"
        assert scraper._get_position_name(3, element_types) == "MID"
        assert scraper._get_position_name(4, element_types) == "FWD"
        assert scraper._get_position_name(99, element_types) == "UNK"  # Unknown position
    
    def test_get_team_name(self, scraper, mock_fpl_data):
        """Test team name mapping."""
        teams = mock_fpl_data["teams"]
        
        assert scraper._get_team_name(1, teams) == "Test Team"
        assert scraper._get_team_name(99, teams) == "Unknown"  # Unknown team
    
    def test_convert_price(self, scraper):
        """Test FPL price conversion."""
        assert scraper._convert_price(85) == 8.5  # FPL format to decimal
        assert scraper._convert_price(100) == 10.0
        assert scraper._convert_price(45) == 4.5
    
    def test_validate_data_valid(self, scraper, mock_fpl_data):
        """Test data validation with valid data."""
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
            ],
            "teams": [
                {
                    "id": 1,
                    "name": "Test Team",
                    "short_name": "TST"
                }
            ]
        }
        
        assert scraper.validate_data(data) is True
    
    def test_validate_data_invalid(self, scraper):
        """Test data validation with invalid data."""
        # Missing required fields
        data = {
            "players": [
                {
                    "name": "Test Player"
                    # Missing id, team, position, etc.
                }
            ]
        }
        
        assert scraper.validate_data(data) is False
        
        # Empty data
        assert scraper.validate_data({}) is False
        assert scraper.validate_data({"players": [], "teams": []}) is False
    
    @pytest.mark.asyncio
    async def test_scrape_with_rate_limiting(self, scraper, mock_fpl_data):
        """Test scraping with rate limiting integration."""
        with patch.object(scraper, '_make_request') as mock_request:
            mock_request.return_value = mock_fpl_data
            
            # Mock rate limiter
            with patch.object(scraper.rate_limiter, 'acquire') as mock_rate_limit:
                result = await scraper.scrape()
                
                # Verify rate limiting was applied
                mock_rate_limit.assert_called_once_with("fpl")
                
                # Verify result
                assert "players" in result
                assert "teams" in result
    
    @pytest.mark.asyncio
    async def test_scrape_with_retry_logic(self, scraper, mock_fpl_data):
        """Test scraping with retry logic integration."""
        with patch.object(scraper, '_make_request') as mock_request:
            # First call fails, second succeeds
            mock_request.side_effect = [Exception("Network error"), mock_fpl_data]
            
            # Mock retry handler
            with patch.object(scraper.retry_handler, 'execute_with_retry') as mock_retry:
                mock_retry.return_value = mock_fpl_data
                
                result = await scraper.scrape()
                
                # Verify retry logic was used
                mock_retry.assert_called_once()
                
                # Verify result
                assert "players" in result
                assert "teams" in result


class TestFPLPlayer:
    """Test cases for FPLPlayer model."""
    
    def test_player_creation(self):
        """Test FPLPlayer model creation."""
        player_data = {
            "id": 1,
            "first_name": "Test",
            "second_name": "Player",
            "web_name": "T. Player",
            "team": 1,
            "element_type": 3,
            "total_points": 100,
            "now_cost": 85,
            "form": "7.5"
        }
        
        player = FPLPlayer(**player_data)
        
        assert player.id == 1
        assert player.first_name == "Test"
        assert player.second_name == "Player"
        assert player.web_name == "T. Player"
        assert player.team == 1
        assert player.element_type == 3
        assert player.total_points == 100
        assert player.now_cost == 85
        assert player.form == "7.5"
    
    def test_player_validation(self):
        """Test FPLPlayer model validation."""
        # Valid player
        valid_data = {
            "id": 1,
            "first_name": "Test",
            "second_name": "Player",
            "web_name": "T. Player",
            "team": 1,
            "element_type": 3,
            "total_points": 100,
            "now_cost": 85,
            "form": "7.5"
        }
        
        player = FPLPlayer(**valid_data)
        assert player is not None
        
        # Invalid player (missing required fields)
        with pytest.raises(Exception):
            FPLPlayer(id=1)  # Missing other required fields


class TestFPLTeam:
    """Test cases for FPLTeam model."""
    
    def test_team_creation(self):
        """Test FPLTeam model creation."""
        team_data = {
            "id": 1,
            "name": "Test Team",
            "short_name": "TST",
            "strength": 4,
            "strength_overall_home": 1200,
            "strength_overall_away": 1100
        }
        
        team = FPLTeam(**team_data)
        
        assert team.id == 1
        assert team.name == "Test Team"
        assert team.short_name == "TST"
        assert team.strength == 4
        assert team.strength_overall_home == 1200
        assert team.strength_overall_away == 1100
    
    def test_team_validation(self):
        """Test FPLTeam model validation."""
        # Valid team
        valid_data = {
            "id": 1,
            "name": "Test Team",
            "short_name": "TST",
            "strength": 4
        }
        
        team = FPLTeam(**valid_data)
        assert team is not None
        
        # Invalid team (missing required fields)
        with pytest.raises(Exception):
            FPLTeam(id=1)  # Missing other required fields 