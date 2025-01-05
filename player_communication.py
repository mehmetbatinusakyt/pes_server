
import json
import logging
from typing import Dict, List

class PlayerCommunication:
    def __init__(self):
        self.connected_players = {}
        self.logger = logging.getLogger('player_communication')

    def register_player(self, player_id: str, client_socket) -> None:
        self.connected_players[player_id] = client_socket
        self.logger.info(f"Player {player_id} registered")

    def broadcast_to_team(self, team: List[str], message: Dict) -> None:
        for player_id in team:
            if player_id in self.connected_players:
                try:
                    self.connected_players[player_id].send(json.dumps(message).encode())
                except Exception as e:
                    self.logger.error(f"Failed to send message to player {player_id}: {e}")

    def send_to_player(self, player_id: str, message: Dict) -> bool:
        if player_id in self.connected_players:
            try:
                self.connected_players[player_id].send(json.dumps(message).encode())
                return True
            except Exception as e:
                self.logger.error(f"Failed to send message to player {player_id}: {e}")
        return False

    def remove_player(self, player_id: str) -> None:
        if player_id in self.connected_players:
            del self.connected_players[player_id]
            self.logger.info(f"Player {player_id} removed")