import os
import ssl
import socket
import threading
import logging
import json
from datetime import datetime
from pathlib import Path
from OpenSSL import crypto

logging.basicConfig(
    filename='auth_server.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger('PES_AUTH_SERVER')

class PESAuthServer:
    def __init__(self, host='0.0.0.0', port=50137): 
        self.host = host
        self.port = port
        self.cert_path = Path("certs")
        self.cert_path.mkdir(exist_ok=True)
        self.cert_file = self.cert_path / "server.crt"
        self.key_file = self.cert_path / "server.key"

        if not self.cert_file.exists() or not self.key_file.exists():
            self._generate_certificates()

        self.context = self._setup_ssl_context()

    def _generate_certificates(self):
        key = crypto.PKey()
        key.generate_key(crypto.TYPE_RSA, 2048)

        cert = crypto.X509()
        cert.get_subject().CN = "pes21-pc.konamionline.com"
        cert.set_serial_number(1000)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(365*24*60*60)
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(key)
        cert.sign(key, 'sha256')

        with open(self.cert_file, "wb") as f:
            f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
        with open(self.key_file, "wb") as f:
            f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))

        logger.info("SSL certificates generated successfully")

    def _setup_ssl_context(self):
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(self.cert_file, self.key_file)
        context.minimum_version = ssl.TLSVersion.TLSv1_3
        return context

    def handle_client(self, client_socket, address):
        try:
            logger.info(f"New client connection from {address}")
            auth_response = {
                'status': 'authenticated',
                'timestamp': datetime.now().isoformat(),
                'redirect': {
                    'server': '127.0.0.1',
                    'port': 50138 
                }
            }
            client_socket.send(json.dumps(auth_response).encode())
            logger.info(f"Sent authentication response to {address}")

            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                logger.info(f"Received from {address}: {data[:100]}...")
        except Exception as e:
            logger.error(f"Error handling client {address}: {str(e)}")
        finally:
            client_socket.close()

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            server.bind((self.host, self.port))
            server.listen(5)
            logger.info(f"Auth server starting on {self.host}:{self.port}")

            while True:
                client, address = server.accept()
                client.settimeout(60)

                try:
                    ssl_client = self.context.wrap_socket(client, server_side=True)
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(ssl_client, address)
                    )
                    client_thread.start()
                except ssl.SSLError as e:
                    logger.error(f"SSL Error with {address}: {str(e)}")
                    client.close()
        except Exception as e:
            logger.error(f"Server error: {str(e)}")
        finally:
            server.close()

if __name__ == "__main__":
    auth_server = PESAuthServer()
    auth_server.start()