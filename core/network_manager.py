import socket
import threading
import json
import logging
from typing import Dict, Callable, Optional
from config import NETWORK_CONFIG

class NetworkManager:
    def __init__(self, host: str, port: int, error_handler: Optional[Callable] = None):
        self.host = host
        self.port = port
        self.clients: Dict[str, socket.socket] = {}
        self.handlers = {}
        self.error_handler = error_handler
        self.logger = logging.getLogger('network_manager')
        self.running = True
        
    def start(self):
        """Start the network manager and listen for connections"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.logger.info(f"NetworkManager listening on {self.host}:{self.port}")
            
            while self.running:
                try:
                    client, address = self.server_socket.accept()
                    client_id = self.generate_client_id(address)
                    self.clients[client_id] = client
                    threading.Thread(target=self.handle_client, 
                                  args=(client_id, client)).start()
                except Exception as e:
                    self.logger.error(f"Error accepting connection: {e}")
                    
        except Exception as e:
            self.logger.error(f"Network manager error: {e}")
            if self.error_handler:
                self.error_handler(e, None)
                
    def generate_client_id(self, address) -> str:
        return f"{address[0]}:{address[1]}"
        
    def handle_client(self, client_id: str, client: socket.socket):
        """Handle individual client connections"""
        while self.running:
            try:
                data = client.recv(NETWORK_CONFIG['buffer_size'])
                if not data:
                    break
                    
                message = json.loads(data.decode())
                if 'type' in message and message['type'] in self.handlers:
                    self.handlers[message['type']](message, client)
                    
            except json.JSONDecodeError:
                self.logger.error(f"Invalid JSON from client {client_id}")
            except Exception as e:
                self.logger.error(f"Error handling client {client_id}: {e}")
                break
                
        self.disconnect_client(client_id)
        
    def disconnect_client(self, client_id: str):
        """Clean up disconnected client"""
        if client_id in self.clients:
            try:
                self.clients[client_id].close()
            except:
                pass
            del self.clients[client_id]
            self.logger.info(f"Client {client_id} disconnected")
            
    def register_handler(self, message_type: str, handler: Callable):
        """Register a handler for a specific message type"""
        self.handlers[message_type] = handler
        
    def broadcast(self, message: dict, exclude_client=None):
        """Broadcast message to all connected clients"""
        encoded_message = json.dumps(message).encode()
        for client_id, client in self.clients.items():
            if client != exclude_client:
                try:
                    client.send(encoded_message)
                except Exception as e:
                    self.logger.error(f"Failed to send to client {client_id}: {e}")
                    self.disconnect_client(client_id)
                    
    def broadcast_to_match(self, match_id: str, message: dict):
        """Broadcast message to all clients in a specific match"""
        message['match_id'] = match_id
        self.broadcast(message)
        
    def stop(self):
        """Stop the network manager"""
        self.running = False
        for client_id in list(self.clients.keys()):
            self.disconnect_client(client_id)
        try:
            self.server_socket.close()
        except:
            pass
