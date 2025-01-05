import socket
import threading
import logging
import json
import psutil
from datetime import datetime
from zeroconf import ServiceInfo, Zeroconf
from config import SERVER_CONFIG, NETWORK_CONFIG, DATABASE_CONFIG
from game_server import GameServer
from flask import Flask, jsonify, request, redirect
from flask_cors import CORS
from werkzeug.middleware.dispatcher import DispatcherMiddleware
import mysql.connector
from wp_login import authenticate_wordpress_user, validate_session_token

import os
import pickle
import time

class GameServer:
    def __init__(self):
        self.matches = {}
        self.active_games = {}
        self.load_matches()

    def save_matches(self):
        try:
            with open('matches.dat', 'wb') as f:
                pickle.dump({
                    'matches': self.matches,
                    'active_games': self.active_games
                }, f)
            logging.info("Matches saved successfully")
        except Exception as e:
            logging.error(f"Error saving matches: {e}")

    def load_matches(self):
        if os.path.exists('matches.dat'):
            try:
                with open('matches.dat', 'rb') as f:
                    data = pickle.load(f)
                    self.matches = data.get('matches', {})
                    self.active_games = data.get('active_games', {})
                logging.info("Matches loaded successfully")
            except Exception as e:
                logging.error(f"Error loading matches: {e}")
        
    def create_match(self, home_team, away_team):
        match_id = len(self.matches) + 1
        self.matches[match_id] = {
            'home_team': home_team,
            'away_team': away_team,
            'score': [0, 0],
            'status': 'waiting',
            'start_time': None,
            'end_time': None
        }
        return match_id

    def start_match(self, match_id):
        try:
            if match_id in self.matches:
                self.matches[match_id]['status'] = 'active'
                self.matches[match_id]['start_time'] = time.time()
                self.active_games[match_id] = self.matches[match_id]
                logging.info(f"Match {match_id} started")
            else:
                logging.warning(f"Attempted to start non-existent match {match_id}")
        except Exception as e:
            logging.error(f"Error starting match {match_id}: {e}")

    def update_score(self, match_id, home_score, away_score):
        try:
            if match_id in self.active_games:
                self.active_games[match_id]['score'] = [home_score, away_score]
                logging.info(f"Match {match_id} score updated: {home_score}-{away_score}")
            else:
                logging.warning(f"Attempted to update score for non-active match {match_id}")
        except Exception as e:
            logging.error(f"Error updating score for match {match_id}: {e}")

    def end_match(self, match_id):
        try:
            if match_id in self.active_games:
                self.active_games[match_id]['status'] = 'ended'
                self.active_games[match_id]['end_time'] = time.time()
                logging.info(f"Match {match_id} ended")
                del self.active_games[match_id]
            else:
                logging.warning(f"Attempted to end non-active match {match_id}")
        except Exception as e:
            logging.error(f"Error ending match {match_id}: {e}")

class TeamLobbyServer:
    def __init__(self, host='127.0.0.1', udp_port1=50000, udp_port2=50001):
        self.host = host
        self.udp_port1 = udp_port1
        self.udp_port2 = udp_port2
        self.port = 5739  # Main TCP port
        self.proxy_port = 5740  # Proxy port
        self.teams = {'home': {}, 'away': {}}
        self.positions = SERVER_CONFIG['positions']
        self.game_server = GameServer()
        self.waiting_players = []
        self.zeroconf = Zeroconf()
        
        # Server monitoring statistics
        self.server_stats = {
            'start_time': datetime.now(),
            'total_connections': 0,
            'active_connections': 0,
            'peak_connections': 0,
            'total_matches': 0,
            'active_matches': 0
        }
        
        # WordPress integration
        self.wp_auth_enabled = DATABASE_CONFIG.get('wp_auth_enabled', False)
        self.wp_session_timeout = DATABASE_CONFIG.get('wp_session_timeout', 3600)
        
        # Initialize Flask API with enhanced CORS support
        self.api = Flask(__name__)
        self.api.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
        
        # Configure CORS with specific settings
        CORS(self.api, resources={
            r"/api/*": {
                "origins": ["https://localhost"],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
                "supports_credentials": True
            }
        })
        
        # Add URL normalization
        @self.api.before_request
        def normalize_url():
            path = request.path
            # Only normalize double slashes
            if '//' in path:
                new_path = path.replace('//', '/')
                return redirect(new_path)
        
        # Database connection - optional
        self.db = None
        self.use_database = False  # Set to True if you want to use MySQL
        if self.use_database:
            try:
                self.db = mysql.connector.connect(
                    host="localhost",
                    user="wp",
                    password="wp",
                    database="wp"
                )
                logging.info("Database connection established successfully")
            except mysql.connector.Error as err:
                logging.error(f"Database connection failed: {err}")
                self.db = None
        
        # Explicitly register routes
        self.api.add_url_rule('/api/admin/status', 'admin_status', self._get_admin_status, methods=['GET'], strict_slashes=False)
        self.api.add_url_rule('/api/user/sync', 'user_sync', self._sync_user_data, methods=['POST'])
        
        @self.api.after_request
        def after_request(response):
            origin = request.headers.get('Origin')
            if origin:
                response.headers.add('Access-Control-Allow-Origin', origin)
            else:
                response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
            response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            if request.method == 'OPTIONS':
                return response, 200
            return response
        
        from datetime import datetime
        # Remove any existing handlers
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
            
        log_filename = f"team_lobby_{datetime.now().strftime('%Y-%m-%d')}.log"
        logging.basicConfig(
            filename=log_filename,
            level=logging.DEBUG,
            format='%(asctime)s - %(message)s'
        )
        self.init_mdns()

    def _sync_user_data(self):
        try:
            user_data = request.get_json()
            if not user_data:
                return jsonify({'error': 'No user data provided'}), 400
            
            # Verify database connection
            if not self.db.is_connected():
                self.db.reconnect()
            
            cursor = self.db.cursor(dictionary=True)
            
            # Check if user exists
            cursor.execute("SELECT id FROM players WHERE id = %s", (user_data['id'],))
            existing_user = cursor.fetchone()
            
            if existing_user:
                # Update existing user
                cursor.execute("""
                    UPDATE players SET
                        username = %s,
                        email = %s,
                        display_name = %s
                    WHERE id = %s
                """, (
                    user_data['username'],
                    user_data['email'],
                    user_data['display_name'],
                    user_data['id']
                ))
            else:
                # Create new user
                cursor.execute("""
                    INSERT INTO players (id, username, email, display_name)
                    VALUES (%s, %s, %s, %s)
                """, (
                    user_data['id'],
                    user_data['username'],
                    user_data['email'],
                    user_data['display_name']
                ))
            
            self.db.commit()
            return jsonify({'message': 'User data synchronized successfully'})
            
        except Exception as e:
            logging.error(f"Error syncing user data: {str(e)}")
            return jsonify({
                'error': 'Internal server error',
                'details': str(e)
            }), 500

    def _get_admin_status(self):
        if not self.use_database or self.db is None:
            # Fallback implementation without database
            return jsonify({
                'total_players': len(self.waiting_players),
                'active_matches': len([m for m in self.game_server.matches.values() if m['status'] == 'active']),
                'banned_players': 0  # Bans not supported without database
            })
        
        try:
            # Verify database connection
            if not self.db.is_connected():
                self.db.reconnect()
            
            cursor = self.db.cursor(dictionary=True)
            
            # Check if players table exists
            cursor.execute("SHOW TABLES LIKE 'players'")
            if not cursor.fetchone():
                logging.warning("Players table does not exist in database")
                return jsonify({
                    'total_players': 0,
                    'active_matches': 0,
                    'banned_players': 0
                })
            
            # Get total players
            cursor.execute("SELECT COUNT(*) as total_players FROM players")
            total_players = cursor.fetchone()['total_players']
            logging.info(f"Found {total_players} total players")
            
            # Get active matches (fallback to 0 if status column doesn't exist)
            try:
                cursor.execute("SELECT COUNT(*) as active_matches FROM matches WHERE status = 'active'")
                active_matches = cursor.fetchone()['active_matches']
                logging.info(f"Found {active_matches} active matches")
            except mysql.connector.Error as err:
                if err.errno == 1054:  # Unknown column error
                    active_matches = 0
                    logging.warning("Status column not found in matches table")
                else:
                    raise
            
            # Get banned players (fallback to 0 if banned column doesn't exist)
            try:
                cursor.execute("SELECT COUNT(*) as banned_players FROM players WHERE banned = 1")
                banned_players = cursor.fetchone()['banned_players']
                logging.info(f"Found {banned_players} banned players")
            except mysql.connector.Error as err:
                if err.errno == 1054:  # Unknown column error
                    banned_players = 0
                    logging.warning("Banned column not found in players table")
                else:
                    raise
            
            return jsonify({
                'total_players': total_players,
                'active_matches': active_matches,
                'banned_players': banned_players
            })
        except mysql.connector.Error as db_error:
            logging.error(f"Database error in _get_admin_status: {db_error}")
            return jsonify({
                'message': 'Database connection error',
                'error': str(db_error)
            }), 500
        except Exception as e:
            logging.error(f"Unexpected error in _get_admin_status: {e}")
            return jsonify({
                'message': 'Internal server error',
                'error': str(e)
            }), 500

    def setup_api_endpoints(self):
        @self.api.route('/')
        def root():
            return jsonify({
                'message': 'PES Server API',
                'endpoints': {
                    '/api/status': 'GET - Get server status',
                    '/api/admin/status': 'GET - Get admin status',
                    '/api/admin/bans': 'GET - Get banned players',
                    '/api/admin/logs': 'GET - Get server logs',
                    '/api/admin/restart': 'POST - Restart server',
                    '/api/admin/shutdown': 'POST - Shutdown server',
                    '/api/admin/players': 'GET - Get connected players'
                }
            }), 200

        @self.api.route('/api/status', methods=['GET'])
        def get_status():
            return jsonify({
                'status': 'online',
                'players': len(self.waiting_players),
                'matches': len(self.game_server.matches),
                'lobbies': len(self.teams['home']) + len(self.teams['away']),
                'uptime': time.time() - self.start_time if hasattr(self, 'start_time') else 0,
                'memory_usage': self.get_memory_usage(),
                'cpu_usage': self.get_cpu_usage()
            })

        @self.api.route('/api/admin/players', methods=['GET'])
        def get_players():
            players = [{
                'id': p['player_id'],
                'status': 'waiting' if p in self.waiting_players else 'in_match',
                'team': self.get_player_team(p['player_id']),
                'position': self.get_player_position(p['player_id'])
            } for p in self.waiting_players]
            return jsonify(players)

        @self.api.route('/api/admin/bans', methods=['GET'])
        def get_bans():
            try:
                if not self.db.is_connected():
                    self.db.reconnect()
                cursor = self.db.cursor(dictionary=True)
                cursor.execute("SELECT * FROM players WHERE banned = 1")
                banned_players = cursor.fetchall()
                return jsonify(banned_players)
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.api.route('/api/admin/logs', methods=['GET'])
        def get_logs():
            try:
                with open('team_lobby.log', 'r') as f:
                    logs = f.read()
                return jsonify({'logs': logs})
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.api.route('/api/admin/restart', methods=['POST'])
        def restart_server():
            try:
                self.server.close()
                self.start()
                return jsonify({'message': 'Server restart initiated'})
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.api.route('/api/admin/shutdown', methods=['POST'])
        def shutdown_server():
            try:
                self.server.close()
                return jsonify({'message': 'Server shutdown initiated'})
            except Exception as e:
                return jsonify({'error': str(e)}), 500

    def get_memory_usage(self):
        import psutil
        process = psutil.Process()
        return process.memory_info().rss

    def get_cpu_usage(self):
        import psutil
        return psutil.cpu_percent()

    def get_player_team(self, player_id):
        for team_name, team in self.teams.items():
            if player_id in team.values():
                return team_name
        return None

    def get_player_position(self, player_id):
        for team in self.teams.values():
            for position, pid in team.items():
                if pid == player_id:
                    return position
        return None

    def start_api_server(self):
        # Load SSL configuration
        ssl_context = None
        try:
            if NETWORK_CONFIG['ssl']['enabled']:
                ssl_context = (
                    NETWORK_CONFIG['ssl']['certfile'],
                    NETWORK_CONFIG['ssl']['keyfile']
                )
                logging.info(f"SSL enabled using cert: {ssl_context[0]}, key: {ssl_context[1]}")
        except Exception as e:
            logging.error(f"Failed to load SSL certificates: {e}")
            ssl_context = None

        self.api_thread = threading.Thread(
            target=self.api.run,
            kwargs={
                'host': self.host,
                'port': self.port,
                'ssl_context': ssl_context
            }
        )
        self.api_thread.daemon = True
        self.api_thread.start()

    def init_mdns(self):
        self.zeroconf = Zeroconf()
        self.service_info = ServiceInfo(
            type_="_pes-teamplay._tcp.local.",
            name="_pes2021._pes-teamplay._tcp.local.",
            addresses=[socket.inet_aton(socket.gethostbyname(socket.gethostname()))],
            port=self.udp_port1
        )

    def register_mdns(self):
        service_type = "_pes-teamplay._tcp.local."
        service_name = "_pes2021._pes-teamplay._tcp.local."
        
        info = ServiceInfo(
            type_=service_type,
            name=service_name,
            addresses=[socket.inet_aton(self.host)],
            port=self.port,
            properties={
                'game': 'PES2021',
                'mode': 'teamplay',
                'version': '1.0',
                'type': '11v11',
                'region': 'EU',
                'max_players': '22',
                'lobby_type': 'ranked',
                'ping': '50'
            }
        )
        
        try:
            self.zeroconf.register_service(info)
            logging.info(f"MDNS service registered: {service_name}")
        except Exception as e:
            logging.error(f"MDNS registration failed: {e}")
            raise

    def handle_client(self, client, address):
        player_id = None
        try:
            while True:
                data = client.recv(1024)
                if not data:
                    break
                    
                # Validate JSON structure
                # Decode incoming data
                decoded_data = data.decode().strip()
                if not decoded_data:
                    error_response = {
                        'error': 'Empty request',
                        'details': 'No data received'
                    }
                    client.send(json.dumps(error_response).encode())
                    continue

                # Handle both HTTP and JSON protocols
                if decoded_data.startswith(('GET ', 'POST ', 'PUT ', 'DELETE ')):
                    logging.info(f"HTTP request from {address}: {decoded_data.splitlines()[0]}")
                    try:
                        # Parse HTTP request
                        headers, body = decoded_data.split('\r\n\r\n', 1)
                        if body:
                            message = json.loads(body)
                            if message['type'] == 'join_lobby':
                                self.handle_join_lobby(client, message)
                            elif message['type'] == 'select_position':
                                self.handle_position_select(client, message)
                            elif message['type'] == 'ready':
                                self.check_match_start(client, message)
                            elif message['type'] == 'reconnect':
                                self.handle_reconnect(client, message)
                            else:
                                raise ValueError("Unknown message type")
                            
                            response = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n"
                            response += json.dumps({'status': 'success'})
                            client.send(response.encode())
                            continue
                    except Exception as e:
                        response = "HTTP/1.1 400 Bad Request\r\nContent-Type: application/json\r\n\r\n"
                        response += json.dumps({
                            'error': 'Invalid request',
                            'details': str(e)
                        })
                        client.send(response.encode())
                        continue
                
                # Handle JSON messages
                try:
                    message = json.loads(decoded_data)
                    if not isinstance(message, dict):
                        raise ValueError("Message must be a JSON object")
                    if 'type' not in message:
                        raise ValueError("Missing required 'type' field")
                        
                    # Validate common fields
                    if 'player_id' in message and not isinstance(message['player_id'], str):
                        raise ValueError("player_id must be a string")
                        
                    if message['type'] == 'join_lobby':
                        if 'player_id' not in message:
                            raise ValueError("Missing player_id in join_lobby")
                        player_id = message['player_id']
                        self.handle_join_lobby(client, message)
                    elif message['type'] == 'select_position':
                        self.handle_position_select(client, message)
                    elif message['type'] == 'ready':
                        self.check_match_start(client, message)
                    elif message['type'] == 'reconnect':
                        if 'player_id' not in message:
                            raise ValueError("Missing player_id in reconnect")
                        player_id = message['player_id']
                        self.handle_reconnect(client, message)
                    else:
                        raise ValueError("Unknown message type")
                        
                except json.JSONDecodeError as e:
                    error_response = {
                        'error': 'Invalid JSON',
                        'details': str(e),
                        'received': decoded_data[:100]  # Truncate long messages
                    }
                    client.send(json.dumps(error_response).encode())
                    continue
                except ValueError as e:
                    error_response = {
                        'error': 'Invalid message format',
                        'details': str(e),
                        'received': decoded_data[:100]  # Truncate long messages
                    }
                    client.send(json.dumps(error_response).encode())
                    continue
        except Exception as e:
            logging.error(f"Client error {address}: {e}")
        finally:
            if player_id:
                self.handle_client_disconnect(player_id)
            client.close()

    def handle_client_disconnect(self, player_id):
        # Remove player from waiting list
        self.waiting_players = [p for p in self.waiting_players if p['player_id'] != player_id]
        
        # Remove player from team positions
        for team in self.teams.values():
            for position, pid in list(team.items()):
                if pid == player_id:
                    del team[position]
                    logging.info(f"Player {player_id} removed from position {position}")
        
        # Check if any matches need to be ended due to player disconnection
        for match_id, match in self.game_server.matches.items():
            if match['status'] == 'active':
                if player_id in match['home_team'].values() or player_id in match['away_team'].values():
                    logging.warning(f"Player {player_id} disconnected from active match {match_id}")
                    self.game_server.end_match(match_id)

    def handle_reconnect(self, client, message):
        player_id = message['player_id']
        # Check if player was in a match
        for match_id, match in self.game_server.matches.items():
            if match['status'] == 'active':
                if player_id in match['home_team'].values() or player_id in match['away_team'].values():
                    # Reconnect player to their position
                    for team in self.teams.values():
                        for position, pid in team.items():
                            if pid == player_id:
                                response = {
                                    'type': 'reconnect_success',
                                    'match_id': match_id,
                                    'team': 'home' if player_id in match['home_team'].values() else 'away',
                                    'position': position
                                }
                                client.send(json.dumps(response).encode())
                                logging.info(f"Player {player_id} reconnected to match {match_id}")
                                return
        # If no active match found
        response = {'type': 'reconnect_failed'}
        client.send(json.dumps(response).encode())
            
    def handle_join_lobby(self, client, message):
        player_id = message['player_id']
        self.waiting_players.append({
            'client': client,
            'player_id': player_id
        })
        response = {
            'type': 'lobby_joined',
            'available_positions': self.positions
        }
        client.send(json.dumps(response).encode())

    def handle_position_select(self, client, message):
        player_id = message['player_id']
        position = message['position']
        team = message['team']
        
        if team in self.teams and position in self.positions:
            if position not in self.teams[team]:
                self.teams[team][position] = player_id
                response = {'type': 'position_confirmed'}
            else:
                response = {'type': 'position_taken'}
        client.send(json.dumps(response).encode())

    def broadcast_match_start(self, match_id):
        match_info = self.game_server.matches[match_id]
        response = {
            'type': 'match_started',
            'match_id': match_id,
            'home_team': match_info['home_team'],
            'away_team': match_info['away_team']
        }
        for player in self.waiting_players:
            try:
                player['client'].send(json.dumps(response).encode())
            except Exception as e:
                logging.error(f"Failed to send match start to player {player['player_id']}: {e}")

    def check_match_start(self, client, message):
        """Check if both teams have 11 players and start match"""
        if len(self.teams['home']) >= 11 and len(self.teams['away']) >= 11:
            # Verify all positions are filled
            home_ready = all(pos in self.teams['home'] for pos in self.positions)
            away_ready = all(pos in self.teams['away'] for pos in self.positions)
            
            if home_ready and away_ready:
                # Create match and assign ports
                match_id = self.game_server.create_match(self.teams['home'], self.teams['away'])
                
                # Assign unique ports for this match
                match_ports = {
                    'home': self.udp_port1,
                    'away': self.udp_port2
                }
                
                # Update match info with ports
                self.game_server.matches[match_id]['ports'] = match_ports
                
                # Broadcast match start with port info
                self.broadcast_match_start(match_id)
                
                # Clear teams for next match
                self.teams = {'home': {}, 'away': {}}

    def start_autosave(self):
        def autosave_loop():
            while True:
                time.sleep(300)  # Save every 5 minutes
                self.game_server.save_matches()
        
        self.autosave_thread = threading.Thread(target=autosave_loop, daemon=True)
        self.autosave_thread.start()

    def start(self):
        try:
            # Try to register MDNS with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.register_mdns()
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        logging.warning(f"MDNS registration failed after {max_retries} attempts: {e}. Continuing without MDNS.")
                    else:
                        time.sleep(1)  # Wait before retrying
            
            # Add socket reuse option
            # Create socket with proper error handling
            try:
                self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            except OSError as e:
                logging.error(f"Socket creation failed: {e}")
                raise
            
            # Setup and start API server
            self.setup_api_endpoints()
            self.start_api_server()
            
            # Start TCP server with proper cleanup
            try:
                # Check if port is available
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    sock.bind((self.host, self.port))
                except OSError as e:
                    logging.error(f"Port {self.port} is already in use: {e}")
                    raise
                
                self.server = sock
                self.server.listen(22)
                print("\nPES server is running\n")
                # Create proxy app for port 5740
                proxy_app = Flask(__name__)
                @proxy_app.route('/', defaults={'path': ''})
                @proxy_app.route('/<path:path>')
                def proxy(path):
                    return redirect(f'http://{self.host}:{self.port}/api/{path}')
                
                # Run both apps using DispatcherMiddleware
                application = DispatcherMiddleware(self.api, {
                    '/api': proxy_app
                })
                
                print(f"Team Lobby Server running on {self.host}:{self.port}")
                print(f"Proxy Server running on {self.host}:{self.proxy_port}")
                
                # Start autosave thread
                self.start_autosave()
                
                while True:
                    client, address = self.server.accept()
                    logging.info(f"New connection from {address}")
                    threading.Thread(target=self.handle_client, args=(client, address)).start()
                    
            except PermissionError as pe:
                logging.error(f"Permission denied for port {self.port}: {pe}")
                raise
            except OSError as oe:
                logging.error(f"Socket error: {oe}")
                raise
                
        except Exception as e:
            logging.error(f"Server error: {e}")
            raise
        finally:
            if hasattr(self, 'server'):
                self.server.close()
                logging.info("Server socket closed")
            self.game_server.save_matches()

if __name__ == "__main__":
    server = TeamLobbyServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nServer shutting down...")
        logging.info("Server shutdown")
