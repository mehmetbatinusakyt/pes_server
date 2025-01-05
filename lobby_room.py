import time
import random
from typing import Dict, List, Optional
import logging
from config import SERVER_CONFIG, MATCHMAKING_CONFIG

class LobbyRoom:
    def __init__(self, lobby_id: str, room_name: str, max_players: int, match_coordinator):
        self.lobby_id = lobby_id
        self.room_name = room_name
        self.max_players = max_players
        self.match_coordinator = match_coordinator
        self.players = {}
        self.teams = {'home': [], 'away': []}
        self.status = 'waiting'
        self.created_at = time.time()
        self.logger = logging.getLogger(f'lobby_{lobby_id}')

    def add_player(self, player_id: str, player_data, team: str) -> bool:
        if len(self.players) >= self.max_players:
            return False
            
        self.players[player_id] = {
            'data': player_data,
            'team': team,
            'position': None,
            'ready': False,
            'joined_at': time.time()
        }
        self.logger.info(f"Player {player_id} joined lobby {self.lobby_id}")
        return True

    def assign_team(self, player_id, team):
        if player_id in self.players and len(self.teams[team]) < SERVER_CONFIG['max_players_per_team']:
            if self.players[player_id]['team']:
                old_team = self.players[player_id]['team']
                self.teams[old_team].remove(player_id)
                
            self.teams[team].append(player_id)
            self.players[player_id]['team'] = team
            return True
        return False

    def set_player_position(self, player_id: str, position: str) -> bool:
        if player_id in self.players and position in SERVER_CONFIG['positions']:
            self.players[player_id]['position'] = position
            self.players[player_id]['ready'] = True
            return True
        return False

    def set_player_ready(self, player_id: str, is_ready: bool) -> bool:
        if player_id in self.players:
            self.players[player_id]['ready'] = is_ready
            return True
        return False

    def check_ready(self):
        if len(self.players) < 2:
            return False
            
        all_ready = all(player['ready'] for player in self.players.values())
        teams_balanced = abs(len(self.teams['home']) - len(self.teams['away'])) <= 1
        
        return all_ready and teams_balanced

    def start_match(self):
        if self.check_ready():
            match_id = self.match_coordinator.create_match(
                self.teams['home'],
                self.teams['away'],
                self.get_player_positions()
            )
            self.status = 'in_match'
            self.logger.info(f"Match {match_id} started from lobby {self.lobby_id}")
            return match_id
        return None

    def get_player_positions(self):
        positions = {'home': {}, 'away': {}}
        for player_id, data in self.players.items():
            if data['team'] and data['position']:
                positions[data['team']][player_id] = data['position']
        return positions

    def remove_player(self, player_id: str) -> bool:
        if player_id in self.players:
            team = self.players[player_id]['team']
            if team and player_id in self.teams[team]:
                self.teams[team].remove(player_id)
            del self.players[player_id]
            self.logger.info(f"Player {player_id} left lobby {self.lobby_id}")
            return True
        return False

    def get_status(self) -> Dict:
        return {
            'id': self.lobby_id,
            'name': self.room_name,
            'players': len(self.players),
            'max_players': self.max_players,
            'status': self.status
        }
