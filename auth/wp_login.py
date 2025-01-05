import requests
import json
import mysql.connector
from config import WORDPRESS_CONFIG
from datetime import datetime, timedelta
import hashlib
import secrets
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.users import GetUserInfo
from wordpress_xmlrpc.methods import posts

# Database connection pool
db_pool = None

def get_db_connection():
    global db_pool
    if db_pool is None:
        db_pool = mysql.connector.connect(
            host=WORDPRESS_CONFIG['db_host'],
            user=WORDPRESS_CONFIG['db_user'],
            password=WORDPRESS_CONFIG['db_password'],
            database=WORDPRESS_CONFIG['db_name'],
            pool_name="wp_pool",
            pool_size=5
        )
    return db_pool

def authenticate_wordpress_user(username, password):
    """Authenticate a WordPress user"""
    url = f"{WORDPRESS_CONFIG['url']}/wp-json/jwt-auth/v1/token"
    try:
        response = requests.post(
            url,
            json={
                'username': username,
                'password': password
            },
            verify=False
        )
        return response.json()
    except Exception as e:
        return {'authenticated': False, 'error': str(e)}

def reset_wordpress_password(username, new_password):
    """Reset a WordPress user's password using proper WordPress hashing"""
    db = get_db_connection()
    cursor = db.cursor()
    
    try:
        # Generate WordPress-compatible password hash
        wp_hasher = hashlib.md5()
        wp_hasher.update(new_password.encode('utf-8'))
        password_hash = wp_hasher.hexdigest()
        
        # Update password in database
        cursor.execute("""
            UPDATE wp_users 
            SET user_pass = %s 
            WHERE user_login = %s
        """, (password_hash, username))
        
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        return False
    finally:
        cursor.close()

def generate_session_token(user_id):
    """Generate secure session token"""
    random_data = secrets.token_bytes(32)
    timestamp = str(int(datetime.now().timestamp()))
    hash_input = f"{user_id}{timestamp}{random_data.hex()}"
    return hashlib.sha256(hash_input.encode()).hexdigest()

def store_user_session(user_id, token):
    """Store user session in database"""
    db = get_db_connection()
    cursor = db.cursor()
    
    try:
        # Delete any existing sessions
        cursor.execute("""
            DELETE FROM wp_sessions 
            WHERE user_id = %s
        """, (user_id,))
        
        # Insert new session
        cursor.execute("""
            INSERT INTO wp_sessions 
            (user_id, token, created_at, expires_at) 
            VALUES (%s, %s, NOW(), DATE_ADD(NOW(), INTERVAL 1 HOUR))
        """, (user_id, token))
        
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        cursor.close()

def validate_session_token(user_id, token):
    """Validate session token"""
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT * FROM wp_sessions 
            WHERE user_id = %s 
            AND token = %s 
            AND expires_at > NOW()
        """, (user_id, token))
        
        session = cursor.fetchone()
        return session is not None
    except Exception as e:
        return False
    finally:
        cursor.close()
