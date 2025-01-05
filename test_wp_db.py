import unittest
from wp_login import wp_login
from config import SERVER_CONFIG
import mysql.connector

class TestWordPressDB(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Test database connection"""
        try:
            cls.connection = mysql.connector.connect(
                host=SERVER_CONFIG['wp_db_host'],
                user=SERVER_CONFIG['wp_db_user'],
                password=SERVER_CONFIG['wp_db_password'],
                database=SERVER_CONFIG['wp_db_name'],
                port=SERVER_CONFIG['wp_db_port']
            )
            cls.cursor = cls.connection.cursor(dictionary=True)
        except Exception as e:
            raise Exception(f"Database connection failed: {e}")

    @classmethod
    def tearDownClass(cls):
        """Close database connection"""
        if cls.connection.is_connected():
            cls.cursor.close()
            cls.connection.close()

    def test_db_connection(self):
        """Test database connection is working"""
        self.assertTrue(self.connection.is_connected())
        
    def test_wp_users_table(self):
        """Test wp_users table exists and has required columns"""
        self.cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'wp_users'
        """, (SERVER_CONFIG['wp_db_name'],))
        
        columns = [row['COLUMN_NAME'] for row in self.cursor.fetchall()]
        required_columns = ['ID', 'user_login', 'user_pass', 'user_email']
        
        for col in required_columns:
            self.assertIn(col, columns)

    def test_wp_login_success(self):
        """Test successful WordPress login"""
        # Create test user
        test_user = {
            'user_login': 'testuser',
            'user_pass': 'testpass123',
            'user_email': 'test@example.com'
        }
        
        # Insert test user
        self.cursor.execute("""
            INSERT INTO wp_users 
            (user_login, user_pass, user_email) 
            VALUES (%s, MD5(%s), %s)
        """, (test_user['user_login'], 
             test_user['user_pass'],
             test_user['user_email']))
        self.connection.commit()
        
        # Test login
        result = wp_login(test_user['user_login'], test_user['user_pass'])
        self.assertIsNotNone(result)
        self.assertEqual(result['user_login'], test_user['user_login'])
        
        # Cleanup
        self.cursor.execute("""
            DELETE FROM wp_users 
            WHERE user_login = %s
        """, (test_user['user_login'],))
        self.connection.commit()

    def test_wp_login_failure(self):
        """Test failed WordPress login"""
        result = wp_login('nonexistent', 'wrongpassword')
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
