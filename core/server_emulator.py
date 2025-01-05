import ssl
import socket
import json
import threading
from datetime import datetime

class PESServerEmulator:
    def __init__(self, host='0.0.0.0', port=443):
        self.host = host
        self.port = port
        self.context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.context.load_cert_chain('certs/server.crt', 'certs/server.key')  # Актуализиран път към сертификатите
        
    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(5)
        
        print(f"PES Server емулатор стартиран на {self.host}:{self.port}")
        
        while True:
            client, address = server.accept()
            client_handler = threading.Thread(
                target=self.handle_client,
                args=(client, address)
            )
            client_handler.start()
            
    def handle_client(self, client_socket, address):
        print(f"Нова връзка от {address}")
        ssl_client = self.context.wrap_socket(client_socket, server_side=True)
        
        try:
            while True:
                data = ssl_client.recv(1024)
                if not data:
                    break
                    
                # Log received data
                print(f"Получени данни от {address}: {data.hex()}")
                
                # Analyze and respond to specific requests
                if b'TEAMPLAYLOBBY' in data:
                    response = {
                        "status": "ok",
                        "timestamp": datetime.now().isoformat(),
                        "server": "PES2021 Emulator",
                        "message": "Team Play Lobby connected"
                    }
                else:
                    response = {
                        "status": "ok",
                        "timestamp": datetime.now().isoformat(),
                        "server": "PES2021 Emulator"
                    }
                
                ssl_client.send(json.dumps(response).encode())
                
        except Exception as e:
            print(f"Грешка при обработка на клиент {address}: {e}")
        finally:
            ssl_client.close()

if __name__ == "__main__":
    server = PESServerEmulator()
    server.start()
