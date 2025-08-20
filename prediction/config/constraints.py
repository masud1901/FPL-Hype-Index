"""
FPL Constraints Configuration

This module defines all FPL rules and constraints that must be satisfied
when generating transfer recommendations.
"""

from dataclasses import dataclass
from typing import Dict, List, Any


@dataclass
class FPLConstraints:
    """FPL game rules and constraints"""
    
    # Squad composition rules
    squad_size: int = 15
    max_players_per_team: int = 3
    min_players_per_position: Dict[str, int] = None
    max_players_per_position: Dict[str, int] = None
    
    # Formation rules
    valid_formations: List[str] = None
    min_defenders: int = 3
    max_defenders: int = 5
    min_midfielders: int = 3
    max_midfielders: int = 5
    min_forwards: int = 1
    max_forwards: int = 3
    
    # Budget constraints
    max_squad_value: float = 100.0
    max_player_value: float = 15.0
    
    # Transfer rules
    free_transfers_per_gameweek: int = 1
    max_transfers_per_gameweek: int = 15  # With hits
    transfer_hit_cost: int = 4  # Points deducted per transfer over free limit
    
    # Captain and vice-captain rules
    captain_multiplier: float = 2.0
    vice_captain_multiplier: float = 1.0
    
    # Bench rules
    bench_size: int = 4
    bench_order_matters: bool = True
    
    def __post_init__(self):
        """Initialize default values"""
        if self.min_players_per_position is None:
            self.min_players_per_position = {
                'GK': 2,
                'DEF': 3,
                'MID': 3,
                'FWD': 1
            }
        
        if self.max_players_per_position is None:
            self.max_players_per_position = {
                'GK': 2,
                'DEF': 5,
                'MID': 5,
                'FWD': 3
            }
        
        if self.valid_formations is None:
            self.valid_formations = [
                '3-4-3', '3-5-2', '4-3-3', '4-4-2', '4-5-1',
                '5-3-2', '5-4-1', '3-6-1', '4-6-0', '5-5-0'
            ]
    
    def validate_squad_composition(self, squad: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate squad composition against FPL rules"""
        errors = []
        warnings = []
        
        # Check squad size
        if len(squad) != self.squad_size:
            errors.append(f"Squad must have exactly {self.squad_size} players")
        
        # Count players by position
        position_counts = {'GK': 0, 'DEF': 0, 'MID': 0, 'FWD': 0}
        team_counts = {}
        total_value = 0.0
        
        for player in squad:
            position = player.get('position', 'MID')
            team = player.get('team', 'Unknown')
            value = player.get('price', 0.0)
            
            position_counts[position] += 1
            team_counts[team] = team_counts.get(team, 0) + 1
            total_value += value
        
        # Check position limits
        for position, count in position_counts.items():
            min_count = self.min_players_per_position.get(position, 0)
            max_count = self.max_players_per_position.get(position, 15)
            
            if count < min_count:
                errors.append(f"Not enough {position} players: {count}/{min_count}")
            elif count > max_count:
                errors.append(f"Too many {position} players: {count}/{max_count}")
        
        # Check team limits
        for team, count in team_counts.items():
            if count > self.max_players_per_team:
                errors.append(f"Too many players from {team}: {count}/{self.max_players_per_team}")
        
        # Check budget
        if total_value > self.max_squad_value:
            errors.append(f"Squad value exceeds limit: {total_value:.1f}/{self.max_squad_value}")
        
        # Check formation validity
        formation = self._get_formation(position_counts)
        if formation not in self.valid_formations:
            warnings.append(f"Formation {formation} may not be optimal")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'formation': formation,
            'total_value': total_value,
            'position_counts': position_counts,
            'team_counts': team_counts
        }
    
    def validate_transfer(self, current_squad: List[Dict], transfers: List[Dict], 
                         budget: float, free_transfers: int) -> Dict[str, Any]:
        """Validate transfer combination"""
        errors = []
        warnings = []
        
        # Check transfer count
        transfer_count = len(transfers)
        if transfer_count > free_transfers:
            transfer_hits = transfer_count - free_transfers
            warnings.append(f"Transfer hits: {transfer_hits} (-{transfer_hits * self.transfer_hit_cost} points)")
        
        # Calculate budget impact
        total_cost = sum(t.get('price', 0.0) for t in transfers)
        if total_cost > budget:
            errors.append(f"Transfers exceed budget: {total_cost:.1f}/{budget}")
        
        # Check if transfers create valid squad
        new_squad = self._apply_transfers(current_squad, transfers)
        squad_validation = self.validate_squad_composition(new_squad)
        
        if not squad_validation['valid']:
            errors.extend(squad_validation['errors'])
        
        warnings.extend(squad_validation['warnings'])
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'transfer_hits': max(0, transfer_count - free_transfers),
            'points_penalty': max(0, transfer_count - free_transfers) * self.transfer_hit_cost,
            'total_cost': total_cost,
            'new_squad': new_squad if len(errors) == 0 else None
        }
    
    def _get_formation(self, position_counts: Dict[str, int]) -> str:
        """Get formation string from position counts"""
        def_count = position_counts.get('DEF', 0)
        mid_count = position_counts.get('MID', 0)
        fwd_count = position_counts.get('FWD', 0)
        return f"{def_count}-{mid_count}-{fwd_count}"
    
    def _apply_transfers(self, current_squad: List[Dict], transfers: List[Dict]) -> List[Dict]:
        """Apply transfers to current squad (simplified)"""
        # This is a simplified implementation
        # In practice, you'd need to match transfers to specific players
        new_squad = current_squad.copy()
        
        # Remove transferred out players and add transferred in players
        for transfer in transfers:
            if 'transfer_out' in transfer:
                # Remove player being transferred out
                new_squad = [p for p in new_squad if p.get('id') != transfer['transfer_out'].get('id')]
            
            if 'transfer_in' in transfer:
                # Add player being transferred in
                new_squad.append(transfer['transfer_in'])
        
        return new_squad
    
    def get_valid_formations(self) -> List[str]:
        """Get list of valid formations"""
        return self.valid_formations.copy()
    
    def is_valid_formation(self, formation: str) -> bool:
        """Check if formation is valid"""
        return formation in self.valid_formations


# Global instance
fpl_constraints = FPLConstraints() 