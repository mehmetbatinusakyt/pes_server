from typing import Dict, List, Optional
import logging
import uuid
from config import MATCH_CONFIG

class MatchCoordinator:
    def __init__(self):
        self.matches = {}
        self.queued_players = []
        self.logger = logging.getLogger('match_coordinator')
        
    def create_match(self, match_id: str) -> bool:
        if match_id not in self.matches:
            self.matches[match_id] = {
                'status': 'waiting',
                'players': [],
                'teams': {'home': [], 'away': []},
                'ready_players': set()
            }
            self.logger.info(f"Created match {match_id}")
            return True
        return False
        
    def add_player_to_match(self, match_id: str, player_id: str, team: str) -> bool:
        if match_id in self.matches:
            match = self.matches[match_id]
            if team in match['teams']:
                if len(match['teams'][team]) < 11:  # Max players per team
                    match['teams'][team].append(player_id)
                    match['players'].append(player_id)
                    self.logger.info(f"Added player {player_id} to {team} in match {match_id}")
                    return True
        return False
        
    def remove_player_from_match(self, match_id: str, player_id: str) -> bool:
        if match_id in self.matches:
            match = self.matches[match_id]
            if player_id in match['players']:
                match['players'].remove(player_id)
                for team in match['teams'].values():
                    if player_id in team:
                        team.remove(player_id)
                if player_id in match['ready_players']:
                    match['ready_players'].remove(player_id)
                return True
        return False
        
    def set_player_ready(self, match_id: str, player_id: str) -> bool:
        if match_id in self.matches:
            match = self.matches[match_id]
            if player_id in match['players']:
                match['ready_players'].add(player_id)
                return True
        return False
        
    def is_match_ready(self, match_id: str) -> bool:
        if match_id in self.matches:
            match = self.matches[match_id]
            return len(match['ready_players']) == len(match['players'])
        return False
