import socket
import struct
import logging
from datetime import datetime
from threading import Thread

class STUNServer:
    def __init__(self, host='0.0.0.0', port=3478, log_level=1, max_requests_per_min=100):
        """
        Initialize STUN server
        :param host: IP address to bind to (default: 0.0.0.0)
        :param port: Port to listen on (default: 3478)
        :param log_level: Logging level (1=INFO, 2=DEBUG, 3=TRACE)
        :param max_requests_per_min: Maximum requests per minute per client (default: 100)
        """
        self.host = host
        self.port = port
        self.log_level = log_level
        self.max_requests_per_min = max_requests_per_min
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.request_counts = {}  # Track request counts per client
        self.last_client_address = None  # Track last client address for validation
        
        # Setup logging
        log_filename = f"logs/stun_server_{datetime.now().strftime('%Y-%m-%d')}.log"
        log_levels = {
            1: logging.INFO,
            2: logging.DEBUG,
            3: logging.DEBUG  # TRACE uses DEBUG level with additional messages
        }
        logging.basicConfig(
            filename=log_filename,
            level=log_levels.get(log_level, logging.INFO),
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Validate configuration
        if not self.validate_config():
            raise ValueError("Invalid STUN server configuration")
        
    def start(self):
        try:
            self.sock.bind((self.host, self.port))
            logging.info(f"STUN server started on {self.host}:{self.port}")
            print(f"STUN server running on {self.host}:{self.port}")
            
            while True:
                data, addr = self.sock.recvfrom(1024)
                Thread(target=self.handle_request, args=(data, addr)).start()
        except Exception as e:
            logging.error(f"STUN server error: {str(e)}")
            print(f"Error: {str(e)}")
            
    def validate_config(self):
        """Validate STUN server configuration"""
        if not isinstance(self.port, int) or self.port < 1024 or self.port > 65535:
            logging.error(f"Invalid port number: {self.port}")
            return False
            
        if not isinstance(self.log_level, int) or self.log_level < 1 or self.log_level > 3:
            logging.error(f"Invalid log level: {self.log_level}")
            return False
            
        try:
            socket.inet_aton(self.host)
        except socket.error:
            logging.error(f"Invalid host address: {self.host}")
            return False
            
        return True

    def _cleanup_rate_limits(self):
        """Cleanup old rate limit counters"""
        now = datetime.now()
        cleanup_threshold = 300  # 5 minutes
        
        # Remove entries older than threshold
        for client_key in list(self.request_counts.keys()):
            if (now - self.request_counts[client_key]['timestamp']).seconds > cleanup_threshold:
                del self.request_counts[client_key]
                if self.log_level > 1:
                    logging.debug(f"Cleaned up rate limit counter for {client_key}")

    def _check_rate_limit(self, addr):
        """Check if client has exceeded rate limit"""
        now = datetime.now()
        client_key = f"{addr[0]}:{addr[1]}"
        
        # Cleanup old counters periodically
        if len(self.request_counts) > 1000:  # Cleanup when we have many clients
            self._cleanup_rate_limits()
            
        # Initialize or update request count
        if client_key not in self.request_counts:
            self.request_counts[client_key] = {
                'count': 1,
                'timestamp': now
            }
            return True
            
        # Reset counter if minute has passed
        if (now - self.request_counts[client_key]['timestamp']).seconds >= 60:
            self.request_counts[client_key] = {
                'count': 1,
                'timestamp': now
            }
            return True
            
        # Increment count and check limit
        self.request_counts[client_key]['count'] += 1
        if self.request_counts[client_key]['count'] > self.max_requests_per_min:
            if self.log_level > 1:
                logging.debug(f"Rate limit exceeded for {client_key}")
            return False
            
        return True

    def _create_error_response(self, error_code, transaction_id):
        """Create STUN Error Response"""
        response = struct.pack('!HH', 0x0111, 0)  # Error response
        response += transaction_id
        response += struct.pack('!HH', 0x0009, 4)  # ERROR-CODE attribute
        response += struct.pack('!H', error_code)
        response += b'\x00\x00'  # Reserved
        return response

    def handle_request(self, data, addr):
        try:
            # Check rate limit
            if not self._check_rate_limit(addr):
                error_response = self._create_error_response(429, b'\x00' * 16)  # 429 = Too Many Requests
                self.sock.sendto(error_response, addr)
                return
                
            # Basic packet validation
            if len(data) < 20:
                if self.log_level > 1:
                    logging.debug(f"Invalid STUN packet length from {addr[0]}:{addr[1]}")
                error_response = self._create_error_response(400, b'\x00' * 16)  # 400 = Bad Request
                self.sock.sendto(error_response, addr)
                return
                
            # Parse STUN message header
            try:
                msg_type = struct.unpack('!H', data[0:2])[0]
                msg_len = struct.unpack('!H', data[2:4])[0]
                transaction_id = data[4:20]
            except struct.error as e:
                if self.log_level > 1:
                    logging.debug(f"STUN packet parsing error from {addr[0]}:{addr[1]}: {str(e)}")
                error_response = self._create_error_response(400, b'\x00' * 16)  # 400 = Bad Request
                self.sock.sendto(error_response, addr)
                return
                
            # Validate message length
            if len(data) != msg_len + 20:
                if self.log_level > 1:
                    logging.debug(f"Invalid STUN packet length from {addr[0]}:{addr[1]}")
                error_response = self._create_error_response(400, transaction_id)  # 400 = Bad Request
                self.sock.sendto(error_response, addr)
                return
                
            # Handle different message types
            if msg_type == 0x0001:  # Binding Request
                # Check if authentication is required
                if not self._validate_message_integrity(data, transaction_id):
                    # Send authentication challenge
                    challenge = self._create_auth_challenge(transaction_id)
                    self.sock.sendto(challenge, addr)
                    
                    if self.log_level > 1:
                        logging.debug(f"Sent authentication challenge to {addr[0]}:{addr[1]}")
                    return
                    
                # Create and send binding response
                response = self._create_binding_response(transaction_id, addr)
                
                # Validate XOR-MAPPED-ADDRESS before sending
                if not self._validate_xor_address(addr, response[20:36]):
                    logging.warning(f"Invalid XOR-MAPPED-ADDRESS from {addr[0]}:{addr[1]}")
                    error_response = self._create_error_response(400, transaction_id)  # 400 = Bad Request
                    self.sock.sendto(error_response, addr)
                    return
                    
                self.sock.sendto(response, addr)
                
                if self.log_level > 1:
                    logging.debug(f"Handled Binding Request from {addr[0]}:{addr[1]}")
            else:
                if self.log_level > 1:
                    logging.debug(f"Unsupported STUN message type {msg_type:04x} from {addr[0]}:{addr[1]}")
                return
                
            logging.info(f"Handled STUN request from {addr[0]}:{addr[1]}")
            
        except struct.error as e:
            if self.log_level > 1:
                logging.debug(f"STUN packet parsing error from {addr[0]}:{addr[1]}: {str(e)}")
        except Exception as e:
            logging.error(f"Error handling STUN request from {addr[0]}:{addr[1]}: {str(e)}")
            
    def _xor_mapped_address(self, transaction_id, addr):
        """Create XOR-MAPPED-ADDRESS attribute"""
        port = addr[1] ^ 0x2112
        ip_bytes = socket.inet_aton(addr[0])
        magic_cookie = b'\x21\x12\xA4\x42'
        xor_ip = bytes([ip_bytes[i] ^ magic_cookie[i % 4] for i in range(4)])
        
        # Store original address for validation
        self.last_client_address = addr
        
        return struct.pack('!HHBBH', 0x0020, 8, 0, 1, port) + xor_ip

    def _validate_xor_address(self, addr, xor_address):
        """Validate that XOR-MAPPED-ADDRESS matches client's real address"""
        if not hasattr(self, 'last_client_address'):
            return False
            
        # Decode XOR-MAPPED-ADDRESS
        try:
            port = struct.unpack('!H', xor_address[4:6])[0] ^ 0x2112
            ip_bytes = bytes([xor_address[i] ^ b'\x21\x12\xA4\x42'[i % 4] 
                           for i in range(4)])
            decoded_ip = socket.inet_ntoa(ip_bytes)
            
            # Compare with original address
            return (decoded_ip == self.last_client_address[0] and 
                   port == self.last_client_address[1])
        except:
            return False

    def _software_attribute(self):
        """Create SOFTWARE attribute"""
        software = "PES2021-STUN/1.0"
        length = len(software)
        return struct.pack('!HH', 0x8022, length) + software.encode('utf-8')

    def _hmac_sha1(self, key, message):
        """Calculate HMAC-SHA1 for message integrity"""
        import hmac
        import hashlib
        return hmac.new(key, message, hashlib.sha1).digest()

    def _create_binding_response(self, transaction_id, addr):
        """Create STUN Binding Success Response"""
        response = struct.pack('!HH', 0x0101, 0)  # Binding success response
        response += transaction_id
        
        # Add XOR-MAPPED-ADDRESS attribute
        response += self._xor_mapped_address(transaction_id, addr)
        
        # Add SOFTWARE attribute
        response += self._software_attribute()
        
        # Add MESSAGE-INTEGRITY if credentials exist
        if hasattr(self, 'shared_secret'):
            # Calculate HMAC-SHA1 over the message
            integrity = self._hmac_sha1(self.shared_secret, response)
            response += struct.pack('!HH', 0x0008, 20)  # MESSAGE-INTEGRITY attribute
            response += integrity
            
        # Update message length
        msg_len = len(response) - 20  # Subtract header length
        response = response[:2] + struct.pack('!H', msg_len) + response[4:]
        
        return response

    def _get_user_credentials(self, username):
        """Retrieve user credentials from WordPress database"""
        try:
            import mysql.connector
            db = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="wp"
            )
            cursor = db.cursor()
            cursor.execute("SELECT user_pass FROM wp_users WHERE user_login = %s", (username,))
            result = cursor.fetchone()
            cursor.close()
            db.close()
            return result[0] if result else None
        except Exception as e:
            logging.error(f"Database error retrieving credentials: {str(e)}")
            return None

    def _validate_credentials(self, username, realm, nonce, response):
        """Validate STUN credentials against WordPress database"""
        password_hash = self._get_user_credentials(username)
        if not password_hash:
            return False
            
        # Calculate expected response
        import hashlib
        ha1 = hashlib.md5(f"{username}:{realm}:{password_hash}".encode()).hexdigest()
        ha2 = hashlib.md5(f"STUN:{nonce}".encode()).hexdigest()
        expected_response = hashlib.md5(f"{ha1}:{nonce}:{ha2}".encode()).hexdigest()
        
        return expected_response == response

    def _generate_nonce(self):
        """Generate a unique nonce value"""
        import secrets
        import time
        return f"{secrets.token_hex(8)}-{int(time.time())}"

    def _create_auth_challenge(self, transaction_id):
        """Create STUN Authentication Challenge"""
        response = struct.pack('!HH', 0x0111, 0)  # Error response
        response += transaction_id
        
        # Add REALM attribute
        realm = "PES2021-STUN"
        response += struct.pack('!HH', 0x0014, len(realm)) + realm.encode('utf-8')
        
        # Add NONCE attribute
        nonce = self._generate_nonce()
        response += struct.pack('!HH', 0x0015, len(nonce)) + nonce.encode('utf-8')
        
        # Add ERROR-CODE attribute (401 Unauthorized)
        response += struct.pack('!HH', 0x0009, 4)  # ERROR-CODE attribute
        response += struct.pack('!H', 401)  # 401 = Unauthorized
        response += b'\x00\x00'  # Reserved
        
        # Update message length
        msg_len = len(response) - 20  # Subtract header length
        response = response[:2] + struct.pack('!H', msg_len) + response[4:]
        
        return response

    def _validate_message_integrity(self, data, transaction_id):
        """Validate MESSAGE-INTEGRITY attribute if present"""
        if not hasattr(self, 'shared_secret'):
            # Check for STUN authentication attributes
            pos = 20  # Skip header
            auth_attrs = {}
            while pos + 4 <= len(data):
                attr_type = struct.unpack('!H', data[pos:pos+2])[0]
                attr_len = struct.unpack('!H', data[pos+2:pos+4])[0]
                
                if attr_type == 0x0006:  # USERNAME
                    auth_attrs['username'] = data[pos+4:pos+4+attr_len].decode('utf-8')
                elif attr_type == 0x0014:  # REALM
                    auth_attrs['realm'] = data[pos+4:pos+4+attr_len].decode('utf-8')
                elif attr_type == 0x0015:  # NONCE
                    auth_attrs['nonce'] = data[pos+4:pos+4+attr_len].decode('utf-8')
                elif attr_type == 0x0008:  # MESSAGE-INTEGRITY
                    auth_attrs['response'] = data[pos+4:pos+4+attr_len].hex()
                    
                pos += 4 + attr_len
                if attr_len % 4 != 0:  # STUN attributes are padded to 4 bytes
                    pos += 4 - (attr_len % 4)
            
            # If authentication attributes present, validate them
            if all(key in auth_attrs for key in ['username', 'realm', 'nonce', 'response']):
                if not self._validate_credentials(
                    auth_attrs['username'],
                    auth_attrs['realm'],
                    auth_attrs['nonce'],
                    auth_attrs['response']
                ):
                    if self.log_level > 1:
                        logging.debug(f"Authentication failed for {auth_attrs['username']} from {addr[0]}:{addr[1]}")
                    return False
                # Store shared secret for future requests
                self.shared_secret = self._get_user_credentials(auth_attrs['username'])
                if self.log_level > 1:
                    logging.debug(f"Authentication successful for {auth_attrs['username']} from {addr[0]}:{addr[1]}")
                return True
                
            # If no auth attributes, send challenge
            return False
            
        # Find MESSAGE-INTEGRITY attribute
        pos = 20  # Skip header
        while pos + 4 <= len(data):
            attr_type = struct.unpack('!H', data[pos:pos+2])[0]
            attr_len = struct.unpack('!H', data[pos+2:pos+4])[0]
            
            if attr_type == 0x0008:  # MESSAGE-INTEGRITY
                # Calculate HMAC over the message up to this point
                expected_hmac = self._hmac_sha1(self.shared_secret, data[:pos])
                received_hmac = data[pos+4:pos+4+attr_len]
                return expected_hmac == received_hmac
                
            pos += 4 + attr_len
            if attr_len % 4 != 0:  # STUN attributes are padded to 4 bytes
                pos += 4 - (attr_len % 4)
                
        return True
            
def run_stun_server():
    server = ST
