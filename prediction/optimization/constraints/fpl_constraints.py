"""
FPL Constraint Checkers

This module contains constraint checkers for FPL squad rules and transfer validation.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd
from utils.logger import get_logger

logger = get_logger(__name__)


class Formation(Enum):
    """Valid FPL formations"""
    F_3_4_3 = "3-4-3"
    F_3_5_2 = "3-5-2"
    F_4_3_3 = "4-3-3"
    F_4_4_2 = "4-4-2"
    F_4_5_1 = "4-5-1"
    F_5_3_2 = "5-3-2"
    F_5_4_1 = "5-4-1"


@dataclass
class SquadConstraints:
    """FPL squad composition constraints"""
    max_players: int = 15
    max_players_per_team: int = 3
    min_goalkeepers: int = 2
    max_goalkeepers: int = 2
    min_defenders: int = 3
    max_defenders: int = 5
    min_midfielders: int = 3
    max_midfielders: int = 5
    min_forwards: int = 1
    max_forwards: int = 3
    budget_limit: float = 100.0
    valid_formations: List[Formation] = None
    
    def __post_init__(self):
        if self.valid_formations is None:
            self.valid_formations = list(Formation)


@dataclass
class TransferConstraints:
    """FPL transfer constraints"""
    free_transfers: int = 1
    max_transfers_per_gw: int = 15
    transfer_cost: float = 4.0
    wildcard_available: bool = False
    free_hit_available: bool = False
    bench_boost_available: bool = False
    triple_captain_available: bool = False


class FPLConstraintChecker:
    """FPL constraint checker for squad validation and transfer optimization"""
    
    def __init__(self, squad_constraints: SquadConstraints, transfer_constraints: TransferConstraints):
        self.squad_constraints = squad_constraints
        self.transfer_constraints = transfer_constraints
        
        # Position mappings
        self.position_mapping = {
            'GK': 'goalkeepers',
            'DEF': 'defenders', 
            'MID': 'midfielders',
            'FWD': 'forwards'
        }
    
    def validate_squad_composition(self, squad: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate squad composition against FPL rules"""
        
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'squad_stats': {}
        }
        
        try:
            # Count players by position
            position_counts = {'GK': 0, 'DEF': 0, 'MID': 0, 'FWD': 0}
            team_counts = {}
            total_cost = 0.0
            
            for player in squad:
                position = player.get('position', '')
                team = player.get('team', '')
                price = player.get('price', 0.0)
                
                if position in position_counts:
                    position_counts[position] += 1
                
                team_counts[team] = team_counts.get(team, 0) + 1
                total_cost += price
            
            # Validate squad size
            total_players = sum(position_counts.values())
            if total_players != self.squad_constraints.max_players:
                validation_result['is_valid'] = False
                validation_result['errors'].append(
                    f"Squad must have exactly {self.squad_constraints.max_players} players, got {total_players}"
                )
            
            # Validate position limits
            if position_counts['GK'] < self.squad_constraints.min_goalkeepers:
                validation_result['is_valid'] = False
                validation_result['errors'].append(
                    f"Must have at least {self.squad_constraints.min_goalkeepers} goalkeepers, got {position_counts['GK']}"
                )
            
            if position_counts['GK'] > self.squad_constraints.max_goalkeepers:
                validation_result['is_valid'] = False
                validation_result['errors'].append(
                    f"Can have at most {self.squad_constraints.max_goalkeepers} goalkeepers, got {position_counts['GK']}"
                )
            
            if position_counts['DEF'] < self.squad_constraints.min_defenders:
                validation_result['is_valid'] = False
                validation_result['errors'].append(
                    f"Must have at least {self.squad_constraints.min_defenders} defenders, got {position_counts['DEF']}"
                )
            
            if position_counts['DEF'] > self.squad_constraints.max_defenders:
                validation_result['is_valid'] = False
                validation_result['errors'].append(
                    f"Can have at most {self.squad_constraints.max_defenders} defenders, got {position_counts['DEF']}"
                )
            
            if position_counts['MID'] < self.squad_constraints.min_midfielders:
                validation_result['is_valid'] = False
                validation_result['errors'].append(
                    f"Must have at least {self.squad_constraints.min_midfielders} midfielders, got {position_counts['MID']}"
                )
            
            if position_counts['MID'] > self.squad_constraints.max_midfielders:
                validation_result['is_valid'] = False
                validation_result['errors'].append(
                    f"Can have at most {self.squad_constraints.max_midfielders} midfielders, got {position_counts['MID']}"
                )
            
            if position_counts['FWD'] < self.squad_constraints.min_forwards:
                validation_result['is_valid'] = False
                validation_result['errors'].append(
                    f"Must have at least {self.squad_constraints.min_forwards} forwards, got {position_counts['FWD']}"
                )
            
            if position_counts['FWD'] > self.squad_constraints.max_forwards:
                validation_result['is_valid'] = False
                validation_result['errors'].append(
                    f"Can have at most {self.squad_constraints.max_forwards} forwards, got {position_counts['FWD']}"
                )
            
            # Validate team limits
            for team, count in team_counts.items():
                if count > self.squad_constraints.max_players_per_team:
                    validation_result['is_valid'] = False
                    validation_result['errors'].append(
                        f"Can have at most {self.squad_constraints.max_players_per_team} players from {team}, got {count}"
                    )
            
            # Validate budget
            if total_cost > self.squad_constraints.budget_limit:
                validation_result['is_valid'] = False
                validation_result['errors'].append(
                    f"Squad cost ({total_cost:.1f}) exceeds budget limit ({self.squad_constraints.budget_limit:.1f})"
                )
            
            # Validate formation
            formation = self._get_formation(position_counts)
            if formation not in self.squad_constraints.valid_formations:
                validation_result['is_valid'] = False
                validation_result['errors'].append(
                    f"Formation {formation.value} is not valid"
                )
            
            # Store squad statistics
            validation_result['squad_stats'] = {
                'total_players': total_players,
                'position_counts': position_counts,
                'team_counts': team_counts,
                'total_cost': total_cost,
                'formation': formation.value,
                'budget_remaining': self.squad_constraints.budget_limit - total_cost
            }
            
            # Add warnings for suboptimal configurations
            if total_cost < self.squad_constraints.budget_limit * 0.9:
                validation_result['warnings'].append(
                    f"Using only {total_cost:.1f} of {self.squad_constraints.budget_limit:.1f} budget"
                )
            
            if len(team_counts) < 8:
                validation_result['warnings'].append(
                    f"Only {len(team_counts)} teams represented, consider more diversity"
                )
            
        except Exception as e:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"Validation error: {str(e)}")
            logger.error(f"Error validating squad composition: {e}")
        
        return validation_result
    
    def validate_transfer(self, current_squad: List[Dict[str, Any]], 
                         transfers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate transfer moves against FPL rules"""
        
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'transfer_cost': 0.0,
            'transfers_made': len(transfers)
        }
        
        try:
            # Count transfers
            num_transfers = len(transfers)
            
            if num_transfers == 0:
                return validation_result
            
            # Check transfer limits
            if num_transfers > self.transfer_constraints.max_transfers_per_gw:
                validation_result['is_valid'] = False
                validation_result['errors'].append(
                    f"Maximum {self.transfer_constraints.max_transfers_per_gw} transfers allowed, got {num_transfers}"
                )
            
            # Calculate transfer cost
            if num_transfers > self.transfer_constraints.free_transfers:
                extra_transfers = num_transfers - self.transfer_constraints.free_transfers
                transfer_cost = extra_transfers * self.transfer_constraints.transfer_cost
                validation_result['transfer_cost'] = transfer_cost
                
                validation_result['warnings'].append(
                    f"Using {extra_transfers} extra transfers, cost: {transfer_cost:.1f} points"
                )
            
            # Validate each transfer
            for i, transfer in enumerate(transfers):
                transfer_validation = self._validate_single_transfer(transfer, i + 1)
                
                if not transfer_validation['is_valid']:
                    validation_result['is_valid'] = False
                    validation_result['errors'].extend(transfer_validation['errors'])
                
                validation_result['warnings'].extend(transfer_validation['warnings'])
            
            # Validate resulting squad
            new_squad = self._apply_transfers(current_squad, transfers)
            squad_validation = self.validate_squad_composition(new_squad)
            
            if not squad_validation['is_valid']:
                validation_result['is_valid'] = False
                validation_result['errors'].extend(squad_validation['errors'])
            
            validation_result['warnings'].extend(squad_validation['warnings'])
            
        except Exception as e:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"Transfer validation error: {str(e)}")
            logger.error(f"Error validating transfers: {e}")
        
        return validation_result
    
    def get_valid_formations(self, position_counts: Dict[str, int]) -> List[Formation]:
        """Get valid formations for given position counts"""
        
        valid_formations = []
        
        for formation in self.squad_constraints.valid_formations:
            if self._is_formation_valid(position_counts, formation):
                valid_formations.append(formation)
        
        return valid_formations
    
    def get_formation_requirements(self, formation: Formation) -> Dict[str, int]:
        """Get position requirements for a specific formation"""
        
        formation_map = {
            Formation.F_3_4_3: {'GK': 2, 'DEF': 3, 'MID': 4, 'FWD': 3},
            Formation.F_3_5_2: {'GK': 2, 'DEF': 3, 'MID': 5, 'FWD': 2},
            Formation.F_4_3_3: {'GK': 2, 'DEF': 4, 'MID': 3, 'FWD': 3},
            Formation.F_4_4_2: {'GK': 2, 'DEF': 4, 'MID': 4, 'FWD': 2},
            Formation.F_4_5_1: {'GK': 2, 'DEF': 4, 'MID': 5, 'FWD': 1},
            Formation.F_5_3_2: {'GK': 2, 'DEF': 5, 'MID': 3, 'FWD': 2},
            Formation.F_5_4_1: {'GK': 2, 'DEF': 5, 'MID': 4, 'FWD': 1}
        }
        
        return formation_map.get(formation, {})
    
    def _get_formation(self, position_counts: Dict[str, int]) -> Formation:
        """Determine formation from position counts"""
        
        def_count = position_counts.get('DEF', 0)
        mid_count = position_counts.get('MID', 0)
        fwd_count = position_counts.get('FWD', 0)
        
        # Map to formation
        if def_count == 3 and mid_count == 4 and fwd_count == 3:
            return Formation.F_3_4_3
        elif def_count == 3 and mid_count == 5 and fwd_count == 2:
            return Formation.F_3_5_2
        elif def_count == 4 and mid_count == 3 and fwd_count == 3:
            return Formation.F_4_3_3
        elif def_count == 4 and mid_count == 4 and fwd_count == 2:
            return Formation.F_4_4_2
        elif def_count == 4 and mid_count == 5 and fwd_count == 1:
            return Formation.F_4_5_1
        elif def_count == 5 and mid_count == 3 and fwd_count == 2:
            return Formation.F_5_3_2
        elif def_count == 5 and mid_count == 4 and fwd_count == 1:
            return Formation.F_5_4_1
        else:
            # Return default formation if no match
            return Formation.F_3_4_3
    
    def _is_formation_valid(self, position_counts: Dict[str, int], formation: Formation) -> bool:
        """Check if position counts match a specific formation"""
        
        requirements = self.get_formation_requirements(formation)
        
        for position, required_count in requirements.items():
            if position_counts.get(position, 0) != required_count:
                return False
        
        return True
    
    def _validate_single_transfer(self, transfer: Dict[str, Any], transfer_number: int) -> Dict[str, Any]:
        """Validate a single transfer move"""
        
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            player_out = transfer.get('player_out')
            player_in = transfer.get('player_in')
            
            if not player_out or not player_in:
                validation_result['is_valid'] = False
                validation_result['errors'].append(
                    f"Transfer {transfer_number}: Both player_out and player_in must be specified"
                )
                return validation_result
            
            # Check if players are different
            if player_out.get('id') == player_in.get('id'):
                validation_result['is_valid'] = False
                validation_result['errors'].append(
                    f"Transfer {transfer_number}: Cannot transfer player to themselves"
                )
            
            # Check if players are from same team (if specified)
            if player_out.get('team') == player_in.get('team'):
                validation_result['warnings'].append(
                    f"Transfer {transfer_number}: Transferring within same team ({player_out.get('team')})"
                )
            
            # Check price constraints
            price_out = player_out.get('price', 0.0)
            price_in = player_in.get('price', 0.0)
            
            if price_in > price_out * 1.5:
                validation_result['warnings'].append(
                    f"Transfer {transfer_number}: Significant price increase ({price_out:.1f} -> {price_in:.1f})"
                )
            
        except Exception as e:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"Transfer {transfer_number} validation error: {str(e)}")
        
        return validation_result
    
    def _apply_transfers(self, current_squad: List[Dict[str, Any]], 
                        transfers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply transfers to current squad"""
        
        new_squad = current_squad.copy()
        
        for transfer in transfers:
            player_out = transfer.get('player_out')
            player_in = transfer.get('player_in')
            
            # Remove player out
            new_squad = [p for p in new_squad if p.get('id') != player_out.get('id')]
            
            # Add player in
            new_squad.append(player_in)
        
        return new_squad 