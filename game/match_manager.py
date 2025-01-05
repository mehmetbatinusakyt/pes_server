import logging
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class Match:
    match_id: int
    home_team: Dict
    away_team: Dict
    score: List[int]
    status: str
    game_time: int = 0
    possession: str = 'home'

class MatchManager:
    def __init__(self):
        self.matches = {}
        self.active_matches = {}
        self.logger = logging.getLogger('match_manager')
        self.match_events = {}
        self.formations = {
            'home': '4-4-2',
            'away': '4-4-2'
        }
        self.match_settings = {}

    def create_match(self, players: List[Dict]) -> int:
        if len(players) != 22:
            raise ValueError("Exactly 22 players required for 11v11 match")
            
        # Sort players by rating
        sorted_players = sorted(players, key=lambda p: p['rating'], reverse=True)
        
        # Create balanced teams using ABBA algorithm
        home_team = []
        away_team = []
        for i, player in enumerate(sorted_players):
            if i % 4 == 0 or i % 4 == 3:
                home_team.append(player)
            else:
                away_team.append(player)
                
        # Calculate average ratings
        home_avg = sum(p['rating'] for p in home_team) / 11
        away_avg = sum(p['rating'] for p in away_team) / 11
        
        # Ensure fair matchmaking
        if abs(home_avg - away_avg) > 100:
            # Rebalance teams if difference is too large
            home_team, away_team = away_team, home_team
            
        match_id = len(self.matches) + 1
        match = Match(
            match_id=match_id,
            home_team={'players': home_team, 'rating': home_avg},
            away_team={'players': away_team, 'rating': away_avg},
            score=[0, 0],
            status='waiting'
        )
        self.matches[match_id] = match
        return match_id

    def start_match(self, match_id: int) -> bool:
        if match_id in self.matches:
            match = self.matches[match_id]
            match.status = 'in_progress'
            self.active_matches[match_id] = match
            self.logger.info(f"Match {match_id} started")
            return True
        return False

    def update_match_state(self, match_id: int, state_update: Dict) -> bool:
        if match_id in self.active_matches:
            match = self.active_matches[match_id]
            if 'score' in state_update:
                match.score = state_update['score']
            if 'game_time' in state_update:
                match.game_time = state_update['game_time']
            if 'possession' in state_update:
                match.possession = state_update['possession']
            return True
        return False

    def update_formation(self, match_id: int, team: str, formation: str) -> bool:
        if match_id in self.matches:
            self.formations[team] = formation
            self.logger.info(f"Team {team} changed formation to {formation}")
            return True
        return False

    def add_match_event(self, match_id: int, event_type: str, event_data: Dict) -> bool:
        if match_id in self.active_matches:
            if match_id not in self.match_events:
                self.match_events[match_id] = []
            
            event = {
                'type': event_type,
                'time': self.active_matches[match_id].game_time,
                'data': event_data
            }
            self.match_events[match_id].append(event)
            return True
        return False

    def initialize_match(self, match_id: int, settings: Dict) -> bool:
        if match_id in self.matches:
            self.match_settings[match_id] = settings
            self.matches[match_id].status = 'initializing'
            return True
        return False

    def synchronize_players(self, match_id: int) -> Dict:
        if match_id in self.matches:
            return {
                'type': 'sync_required',
                'match_id': match_id,
                'settings': self.match_settings[match_id]
            }
        return None
