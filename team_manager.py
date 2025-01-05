from typing import Dict, List, Optional
import logging

class TeamManager:
    def __init__(self):
        self.teams = {'home': {}, 'away': {}}
        self.positions = ['GK', 'LB', 'CB1', 'CB2', 'RB', 'LM', 'CM1', 'CM2', 'RM', 'CF1', 'CF2']
        self.player_positions = {}
        self.logger = logging.getLogger('team_manager')
        self.team_tactics = {
            'home': {'pressure': 50, 'attacking_style': 'possession'},
            'away': {'pressure': 50, 'attacking_style': 'counter'}
        }
        self.team_captains = {'home': None, 'away': None}

    def assign_position(self, player_id: str, team: str, position: str) -> bool:
        if team not in self.teams or position not in self.positions:
            return False
            
        if position in self.teams[team]:
            return False
            
        self.teams[team][position] = player_id
        self.player_positions[player_id] = {'team': team, 'position': position}
        self.logger.info(f"Player {player_id} assigned to {team} as {position}")
        return True

    def get_player_position(self, player_id: str) -> Optional[Dict]:
        return self.player_positions.get(player_id)

    def remove_player(self, player_id: str) -> bool:
        if player_id in self.player_positions:
            position_info = self.player_positions[player_id]
            del self.teams[position_info['team']][position_info['position']]
            del self.player_positions[player_id]
            return True
        return False

    def is_team_complete(self, team: str) -> bool:
        return len(self.teams[team]) >= 11

    def set_team_captain(self, team: str, player_id: str) -> bool:
        if team in self.teams and player_id in self.player_positions:
            self.team_captains[team] = player_id
            self.logger.info(f"Player {player_id} set as captain for team {team}")
            return True
        return False

    def update_team_tactics(self, team: str, tactics: Dict) -> bool:
        if team in self.team_tactics:
            self.team_tactics[team].update(tactics)
            self.logger.info(f"Team {team} updated tactics: {tactics}")
            return True
        return False