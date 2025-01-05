import logging
from typing import Dict
from config import SERVER_CONFIG
from lobby_room import LobbyRoom

class LobbyManager:
    def __init__(self):
        self.logger = logging.getLogger('lobby_manager')
        self.active_lobbies: Dict[str, LobbyRoom] = {}
        self.lobby_timeouts = {}
        
    def create_lobby(self, lobby_id: str, lobby_name: str, match_coordinator) -> LobbyRoom:
        lobby = LobbyRoom(
            lobby_id=lobby_id,
            room_name=lobby_name,
            max_players=SERVER_CONFIG['max_players'],
            match_coordinator=match_coordinator
        )
        self.active_lobbies[lobby_id] = lobby
        self.logger.info(f"Created lobby: {lobby_name} (ID: {lobby_id})")
        return lobby
        
    def remove_lobby(self, lobby_id: str):
        if lobby_id in self.active_lobbies:
            del self.active_lobbies[lobby_id]
            self.logger.info(f"Removed lobby {lobby_id}")
            
    def get_lobby(self, lobby_id: str) -> LobbyRoom:
        return self.active_lobbies.get(lobby_id)
        
    def list_lobbies(self) -> Dict[str, Dict]:
        return {
            lobby_id: {
                'name': lobby.room_name,
                'players': len(lobby.players),
                'max_players': lobby.max_players,
                'status': lobby.status
            }
            for lobby_id, lobby in self.active_lobbies.items()
        }
