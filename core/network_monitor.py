import socket
import threading
import logging
import time
from scapy.all import sniff, IP, TCP, UDP

class NetworkMonitor:
    def __init__(self):
        self.running = True
        self.ports = [50123, 50124]  # High numbered ports
        logging.basicConfig(
            filename='network_monitor.log',
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def packet_callback(self, packet):
        try:
            if TCP in packet:
                if packet[TCP].dport in self.ports:
                    logging.info(f"TCP: {packet[IP].src}:{packet[TCP].sport} -> {packet[IP].dst}:{packet[TCP].dport}")
            elif UDP in packet and packet[UDP].dport == 3702:
                logging.info(f"Discovery: {packet[IP].src} -> {packet[IP].dst}")
        except Exception as e:
            logging.error(f"Packet processing error: {e}")

    def start(self):
        try:
            print("Starting passive network monitor...")
            logging.info("Network monitor started")
            
            # Create filter for our ports
            port_filter = f"port 3702 or port 50123 or port 50124"
            
            # Start packet capture
            sniff(filter=port_filter, 
                  prn=self.packet_callback, 
                  store=0,
                  stop_filter=lambda x: not self.running)
                
        except KeyboardInterrupt:
            self.running = False
            print("\nNetwork monitor stopped")
        except Exception as e:
            logging.error(f"Monitor error: {e}")
            raise

if __name__ == "__main__":
    monitor = NetworkMonitor()
    try:
        monitor.start()
    except Exception as e:
        print(f"Error: {e}")