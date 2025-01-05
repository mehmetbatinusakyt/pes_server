import sys
import os
# Add main project directory to path
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(base_dir)
# Add config directory to path
sys.path.append(os.path.join(base_dir, 'config'))

import mysql.connector
from mysql.connector import Error
from config import SERVER_CONFIG
import hashlib
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('wp_login.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('WP_LOGIN')

def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = mysql.connector.connect(
            host=SERVER_CONFIG['wp_db_host'],
            user=SERVER_CONFIG['wp_db_user'],
            password=SERVER_CONFIG['wp_db_password'],
            database=SERVER_CONFIG['wp_db_name'],
            port=SERVER_CONFIG['wp_db_port']
        )
        return connection
    except Error as e:
        logger.error(f"Database connection error: {e}")
        return None

def wp_login(username: str, password: str) -> dict:
    """
    Authenticate user against WordPress database
    Returns user data if successful, None otherwise
    """
    connection = get_db_connection()
    if not connection:
        return None

    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get user data
        query = """
            SELECT ID, user_login, user_pass, user_email, display_name 
            FROM wp_users 
            WHERE user_login = %s
        """
        cursor.execute(query, (username,))
        user = cursor.fetchone()
        
        if not user:
            logger.debug(f"User not found: {username}")
            return None
            
        # Verify password against WordPress hash
        if not verify_password(password, user['user_pass']):
            logger.debug(f"Invalid password for user: {username}")
            return None
            
        # Return user data without password hash
        return {
            'ID': user['ID'],
            'user_login': user['user_login'],
            'user_email': user['user_email'],
            'display_name': user['display_name']
        }
        
    except Error as e:
        logger.error(f"Database query error: {e}")
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def verify_password(password: str, wp_hash: str) -> bool:
    """
    Verify password against WordPress password hash
    Supports both old MD5 and new phpass hashes
    """
    if wp_hash.startswith('$P$') or wp_hash.startswith('$2y$'):
        # Modern phpass hash
        from phpass import PasswordHash
        hasher = PasswordHash(8, True)
        return hasher.CheckPassword(password, wp_hash)
    else:
        # Old MD5 hash
        return wp_hash == hashlib.md5(password.encode()).hexdigest()

class PasswordHash:
    """PHPass compatible password hashing"""
    def __init__(self, iteration_count_log2=8, portable_hashes=True):
        self.iteration_count_log2 = iteration_count_log2
        self.portable_hashes = portable_hashes
        self.random_state = None
        
    def CheckPassword(self, password, stored_hash):
        """Verify password against stored hash"""
        hash = self.crypt_private(password, stored_hash)
        return hash == stored_hash
        
    def crypt_private(self, password, setting):
        """Main password hashing function"""
        # Implementation of PHPass algorithm
        # ... (implementation details omitted for brevity)
        return hashed_password
