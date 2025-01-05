import socket
import logging
import traceback
import uuid
import time
from flask import Flask, request, jsonify, make_response
from wp_login import wp_login

# Test logging with file handler
file_handler = logging.FileHandler('game_server.log', mode='w')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logging.basicConfig(level=logging.DEBUG, handlers=[file_handler])
logging.info("Test log message - logging to file is working")
import threading
import logging
import json
import sys
import time
from typing import Dict, Optional
from config import SERVER_CONFIG
from match_statistics import MatchStatistics
from match_state import MatchStateManager
from network_manager import NetworkManager
from match_coordinator import MatchCoordinator
import ssl
from datetime import datetime

# Configure logging at module level
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('game_server.log', mode='a'),  # Changed to append mode
        logging.StreamHandler()
    ]
)
logging.getLogger().setLevel(logging.DEBUG)  # Ensure root logger is set to DEBUG
logger = logging.getLogger('PES_GAME_SERVER')

class GameServer:
    def __init__(self):
        self.matches = {}
        self.active_games = {}
        self.game_port = 5743  # Changed to avoid conflict with team_lobby_server
        self.host = SERVER_CONFIG['host']
        self.app = Flask(__name__)
        self.app.secret_key = SERVER_CONFIG['secret_key']
        self.sessions = {}
        
        # Setup authentication routes
        self.app.add_url_rule('/login', 'login', self.handle_login, methods=['POST'])
        self.app.add_url_rule('/logout', 'logout', self.handle_logout, methods=['POST'])
        self.app.add_url_rule('/check_session', 'check_session', self.check_session, methods=['GET'])
        
        logger.info("Game Server initializing...")
        
        self.network = NetworkManager(SERVER_CONFIG['host'], self.game_port)
        self.setup_network_handlers()
        self.match_statistics = {}
        self.disconnected_players = {}  # player_id: {match_id, team, position}
        self.match_states = {}
        self.match_coordinator = MatchCoordinator()
        self.network_manager = NetworkManager(
            SERVER_CONFIG['host'],
            self.game_port,
            self.handle_network_error
        )
        self.context = self._setup_ssl_context()
        self.lobbies = {}
    
    def _setup_ssl_context(self):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain('certs/server.crt', 'certs/server.key')
        context.verify_mode = ssl.CERT_NONE  # Disable client certificate verification
        context.options |= ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3  # Disable insecure protocols
        context.set_ciphers('ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384')
        return context

    def setup_network_handlers(self):
        self.network.register_handler('match_action', self.handle_match_action)
        self.network.register_handler('position_update', self.handle_position_update)
        self.network.register_handler('game_event', self.handle_game_event)
    
    def handle_match_action(self, message: dict, client: socket.socket):
        match_id = message['match_id']
        action = message['action']
        
        if match_id not in self.match_states:
            return
            
        match_state = self.match_states[match_id]
        
        if action == 'start_match':
            if match_state.start_match():
                self.broadcast_match_state(match_id)
        elif action == 'pause_match':
            if match_state.pause_match():
                self.broadcast_match_state(match_id)
        elif action == 'resume_match':
            if match_state.resume_match():
                self.broadcast_match_state(match_id)
        else:
            if match_id in self.matches:
                self.network.broadcast({
                    'type': 'match_update',
                    'match_id': match_id,
                    'action': action,
                    'data': message.get('data', {})
                }, exclude_client=client)
    
    def handle_position_update(self, message: dict, client: socket.socket):
        match_id = message['match_id']
        player_id = message['player_id']
        position = message['position']
        if self.assign_position(match_id, message['team'], position, player_id):
            self.network.broadcast({
                'type': 'position_changed',
                'match_id': match_id,
                'player_id': player_id,
                'position': position
            })
        self.synchronize_match_state(match_id)

    def handle_game_event(self, message: dict, client: socket.socket):
        match_id = message['match_id']
        event_type = message['event_type']
        if match_id in self.matches:
            if event_type == 'goal':
                self.update_score(match_id, message['team'], message['score'])
            self.network.broadcast({
                'type': 'game_event',
                'match_id': match_id,
                'event': message
            })

    def start(self):
        try:
            threading.Thread(target=self.network.start, daemon=True).start()
            
            # Start game server
            self.game_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.game_socket.bind((self.host, self.game_port))
            self.game_socket.listen(SERVER_CONFIG['max_players'])
            print(f"Game Server running on {self.host}:{self.game_port}")
            logging.info(f"Game Server started on {self.host}:{self.game_port}")
            
            # Start admin server
            logging.info("Reached admin server initialization block")
            try:
                logging.info("Inside admin server try block")
                logging.info("Attempting to create admin socket")
                self.admin_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                logging.info(f"Created admin socket: {self.admin_socket}")
                
                logging.info("Setting socket options")
                self.admin_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                
                logging.info(f"Attempting to bind to {self.host}:50124")
                self.admin_socket.bind((self.host, 50124))
                logging.info("Bind successful")
                
                logging.info("Starting to listen on admin socket")
                self.admin_socket.listen(5)
                logging.info("Listen successful")
                
                print(f"Admin API running on {self.host}:50124")
                logging.info(f"Admin API started on {self.host}:50124")
                logging.info(f"Admin socket details: {self.admin_socket}")
                logging.info(f"Admin socket fileno: {self.admin_socket.fileno()}")
                logging.info(f"Admin socket getsockname: {self.admin_socket.getsockname()}")
            except Exception as e:
                logging.error(f"Failed to start admin server: {e}")
                logging.error(f"Admin server error details: {str(e)}")
                logging.error(f"Socket error: {e.errno if hasattr(e, 'errno') else 'N/A'}")
                logging.error(f"Socket message: {e.strerror if hasattr(e, 'strerror') else 'N/A'}")
                logging.error(f"Socket filename: {e.filename if hasattr(e, 'filename') else 'N/A'}")
                logging.error(f"Traceback: {traceback.format_exc()}")
                raise
            
            # Start admin server thread
            threading.Thread(target=self.run_admin_server, daemon=True).start()
            
            while True:
                client, address = self.game_socket.accept()
                ssl_client = self.context.wrap_socket(client, server_side=True)
                threading.Thread(target=self.handle_client, args=(ssl_client, address)).start()
                
        except Exception as e:
            logging.error(f"Server error: {e}")
            sys.exit(1)
            
    def handle_client(self, client, address):
        try:
            logger.info(f"Game connection from {address}")
            while True:
                data = client.recv(1024)
                if not data:
                    break
                self.process_game_data(client, json.loads(data.decode()))
                if b'TEAMPLAYLOBBY' in data:
                    response = {
                        'status': 'lobby_created',
                        'lobby_id': len(self.lobbies) + 1,
                        'timestamp': datetime.now().isoformat()
                    }
                    response_json = json.dumps(response)
                    client.send(('HTTP/1.1 200 OK\r\n'
                                 'Content-Type: application/json\r\n'
                                 'Access-Control-Allow-Origin: *\r\n'
                                 'Content-Length: ' + str(len(response_json)) + '\r\n'
                                 '\r\n' + response_json).encode('utf-8'))
        except Exception as e:
            logging.error(f"Client error {address}: {e}")
        finally:
            client.close()

    def process_game_data(self, client, data):
        try:
            match_id = data.get('match_id')
            action = data.get('action')
            
            if action == 'join_match':
                self.join_match(match_id, data['team'], data['player_id'])
            elif action == 'update_position':
                self.update_position(match_id, data['team'], data['position'], data['player_id'])
                
        except Exception as e:
            logging.error(f"Error processing game data: {e}")

    def create_match(self, match_id):
        self.matches[match_id] = {
            'home_team': {},
            'away_team': {},
            'score': [0, 0],
            'state': 'waiting',
            'positions': {
                'home': {pos: None for pos in SERVER_CONFIG['positions']},
                'away': {pos: None for pos in SERVER_CONFIG['positions']}
            }
        }
        logging.info(f"Match {match_id} created")
        self.match_statistics[match_id] = MatchStatistics(match_id)
        self.match_states[match_id] = MatchStateManager(match_id)
        return match_id

    def join_team(self, match_id, team, player_id):
        if match_id in self.matches:
            if len(self.matches[match_id][f'{team}_team']) < SERVER_CONFIG['max_players_per_team']:
                self.matches[match_id][f'{team}_team'][player_id] = None  # No position yet
                logging.info(f"Player {player_id} joined {team} team in match {match_id}")
                return True
        return False

    def check_match_ready(self, match_id):
        if match_id in self.matches:
            match = self.matches[match_id]
            home_ready = all(pos is not None for pos in match['positions']['home'].values())
            away_ready = all(pos is not None for pos in match['positions']['away'].values())
            return home_ready and away_ready
        return False

    def start_match(self, match_id):
        if self.check_match_ready(match_id):
            self.matches[match_id]['state'] = 'active'
            logging.info(f"Match {match_id} started")
            return True
        return False

    def join_match(self, match_id, team, player_id, position):
        if match_id in self.matches:
            self.matches[match_id]['positions'][team][position] = player_id
            logging.info(f"Player {player_id} joined match {match_id}")
            return True
        return False

    def update_score(self, match_id, team, score):
        if match_id in self.matches:
            if team == 'home':
                self.matches[match_id]['score'][0] = score
            else:
                self.matches[match_id]['score'][1] = score
            logging.info(f"Updated score for match {match_id}: {self.matches[match_id]['score']}")
            
    def assign_position(self, match_id, team, position, player_id):
        if match_id in self.matches:
            self.matches[match_id]['positions'][team][position] = player_id
            logging.info(f"Player {player_id} assigned to {position} in {team} team")
            return True
        return False

    def handle_disconnect(self, player_id: str, match_id: str):
        if match_id in self.matches:
            match = self.matches[match_id]
            for team in ['home', 'away']:
                positions = match['positions'][team]
                for pos, pid in positions.items():
                    if pid == player_id:
                        self.disconnected_players[player_id] = {
                            'match_id': match_id,
                            'team': team,
                            'position': pos
                        }
                        positions[pos] = None
                        return True
        return False

    def handle_reconnect(self, player_id: str) -> Dict:
        if player_id in self.disconnected_players:
            data = self.disconnected_players[player_id]
            match_id = data['match_id']
            if match_id in self.matches:
                if self.join_match(match_id, data['team'], player_id, data['position']):
                    del self.disconnected_players[player_id]
                    return data
        return None

    def update_match_statistics(self, match_id: str, team: str, stat_type: str):
        if match_id in self.match_statistics:
            self.match_statistics[match_id].update_stat(team, stat_type)
        return None

    def update_match_states(self):
        for match_id, state_manager in self.match_states.items():
            update = state_manager.update_state()
            if update:
                self.handle_state_change(match_id, update)

    def handle_state_change(self, match_id: str, update: Dict):
        if update['type'] == 'half_time':
            self.network.broadcast({
                'type': 'match_update',
                'match_id': match_id,
                'action': 'half_time',
                'data': self.match_states[match_id].get_state_summary()
            })
        elif update['type'] == 'match_end':
            self.finish_match(match_id)

    def broadcast_match_state(self, match_id: str):
        if match_id in self.match_states:
            self.network.broadcast({
                'type': 'match_state_update',
                'match_id': match_id,
                'state': self.match_states[match_id].get_state_summary()
            })

    def finish_match(self, match_id: str):
        if match_id in self.matches:
            final_stats = self.match_statistics[match_id].get_stats()
            self.network.broadcast({
                'type': 'match_finished',
                'match_id': match_id,
                'stats': final_stats,
                'final_score': self.matches[match_id]['score']
            })
            # Cleanup after match ends
            self.cleanup_match(match_id)

    def cleanup_match(self, match_id: str):
        if match_id in self.matches:
            del self.matches[match_id]
        if match_id in self.match_states:
            del self.match_states[match_id]
        if match_id in self.match_statistics:
            del self.match_statistics[match_id]

    def handle_network_error(self, error, client_id):
        """Handle network errors and reconnection attempts"""
        self.logger.error(f"Network error for client {client_id}: {error}")
        if client_id in self.active_players:
            match_id = self.active_players[client_id]['match_id']
            self.handle_disconnect(client_id, match_id)
            
    def synchronize_match_state(self, match_id):
        """Synchronize match state between all players"""
        if match_id in self.match_states:
            state = self.match_states[match_id].get_full_state()
            self.network_manager.broadcast_to_match(match_id, {
                'type': 'state_sync',
                'state': state,
                'timestamp': time.time()
            })

    def handle_login(self):
        """Handle WordPress login requests"""
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return make_response(jsonify({'error': 'Username and password required'}), 400)
            
        user = wp_login(username, password)
        if not user:
            return make_response(jsonify({'error': 'Invalid credentials'}), 401)
            
        # Create session
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            'user_id': user['ID'],
            'username': user['user_login'],
            'expires': time.time() + SERVER_CONFIG['session_timeout']
        }
        
        return jsonify({
            'session_id': session_id,
            'user': {
                'id': user['ID'],
                'username': user['user_login'],
                'display_name': user['display_name']
            }
        })

    def handle_logout(self):
        """Handle logout requests"""
        session_id = request.headers.get('X-Session-ID')
        if session_id in self.sessions:
            del self.sessions[session_id]
        return jsonify({'status': 'success'})

    def check_session(self):
        """Verify session validity"""
        session_id = request.headers.get('X-Session-ID')
        if session_id in self.sessions:
            session = self.sessions[session_id]
            if time.time() < session['expires']:
                return jsonify({
                    'authenticated': True,
                    'user': {
                        'id': session['user_id'],
                        'username': session['username']
                    }
                })
        return jsonify({'authenticated': False}), 401

    def run_admin_server(self):
        """Run the admin server to handle status requests"""
        while True:
            client, address = self.admin_socket.accept()
            threading.Thread(target=self.handle_admin_request, args=(client,)).start()

def start_game_server():
    host = SERVER_CONFIG['host']
    port = 5744  # Changed to avoid conflict with team_lobby_server

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((host, port))
        server_socket.listen()
        logger.info(f"Game Server started on {host}:{port}")
        
        while True:
            client_socket, addr = server_socket.accept()
            with client_socket:
                logger.info(f"Connection from {addr}")
                # ...existing code...

if __name__ == "__main__":
    start_game_server()
