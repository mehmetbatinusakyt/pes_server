import sys
import os
# Add main project directory to path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)
# Add config directory to path
sys.path.append(os.path.join(base_dir, 'config'))
# Add auth directory to path 
sys.path.append(os.path.join(base_dir, 'auth'))
import mysql.connector
from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
import datetime
from process_manager import ProcessManager

def create_app():
    app = Flask(__name__)
    CORS(app, resources={
        r"/api/*": {
            "origins": ["https://localhost"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    @app.route('/', methods=['GET'])
    @app.route('/index', methods=['GET'])
    def index():
        # Explicit response with no redirects
        return "PES Server is running", 200, {
            'Content-Type': 'text/plain; charset=utf-8',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
        
    @app.route('/<path:path>', methods=['GET'])
    def catch_all(path):
        return f"Invalid path: /{path}", 404
        
    @app.before_request
    def log_routes():
        if not hasattr(app, 'routes_logged'):
            logger.info("Registered routes:")
            for rule in app.url_map.iter_rules():
                logger.info(f"{rule.endpoint}: {rule.rule} ({sorted(rule.methods)})")
            app.routes_logged = True
            
    # Disable all automatic redirects
    app.url_map.strict_slashes = False
    app.url_map.redirect_defaults = False
    
    return app

# Initialize process manager
process_manager = ProcessManager()

# Start required processes
process_manager.start_process('wp_login', 'python auth/wp_login.py')
process_manager.start_process('game_server', 'python core/game_server.py') 
process_manager.start_process('network_manager', 'python core/network_manager.py')
process_manager.start_process('lobby_manager', 'python game/lobby_manager.py')

app = create_app()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler('pes_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_db_connection():
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="wp",
            password="wp",
            database="wp"
        )
        cursor = db.cursor()
        cursor.execute("SHOW TABLES LIKE 'players'")
        if not cursor.fetchone():
            logger.error("Players table does not exist")
            return None
            
        cursor.execute("SHOW TABLES LIKE 'matches'")
        if not cursor.fetchone():
            logger.error("Matches table does not exist")
            return None
            
        return db
    except mysql.connector.Error as err:
        logger.error(f"Database connection error: {err}")
        return None
    except Exception as e:
        logger.error(f"Unexpected database error: {e}")
        return None

@app.route('/api/admin/status/', methods=['GET'])
@app.route('/api/admin/status', methods=['GET'])
def admin_status():
    db = get_db_connection()
    if not db:
        return jsonify({'error': 'Database connection failed'}), 500
        
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as total_players FROM players")
        result = cursor.fetchone()
        if not result or 'total_players' not in result:
            return jsonify({'error': 'Invalid players count result'}), 500
        total_players = result['total_players']
        
        cursor.execute("SELECT COUNT(*) as active_matches FROM matches")
        result = cursor.fetchone()
        if not result or 'active_matches' not in result:
            return jsonify({'error': 'Invalid matches count result'}), 500
        active_matches = result['active_matches']
        
        return jsonify({
            'total_players': total_players,
            'active_matches': active_matches,
            'banned_players': 0
        })
    except mysql.connector.Error as err:
        logger.error(f"Database query error: {err}")
        return jsonify({'error': str(err)}), 500
    except Exception as e:
        logger.error(f"Unexpected error in admin_status: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if db:
            db.close()

@app.route('/api/game/connect/', methods=['POST'])
def game_connect():
    try:
        data = request.get_json()
        if not data or 'version' not in data or 'player_id' not in data:
            return jsonify({'error': 'Invalid request'}), 400
            
        if data['version'] != '2021':
            return jsonify({'error': 'Unsupported game version'}), 400
            
        return jsonify({
            'status': 'connected',
            'server_time': datetime.datetime.now().isoformat(),
            'matchmaking_url': 'http://127.0.0.1:5739/api/matchmaking/'
        })
        
    except Exception as e:
        logger.error(f"Game connection error: {e}")
        return jsonify({'error': 'Connection failed'}), 500

@app.route('/api/debug/routes/')
def debug_routes():
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': sorted(rule.methods),
            'path': rule.rule
        })
    return jsonify(routes)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5739)
