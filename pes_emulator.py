from scapy.all import *
import logging
import json
from datetime import datetime
from scapy.layers.dns import DNS, DNSQR, DNSRR

# Configure logging
logging.basicConfig(
    filename='pes_emulator.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# Suppress Scapy warnings
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

def create_dns_response(packet):
    """Create DNS response for PES server queries"""
    if DNSQR in packet and packet[DNSQR].qname:
        qname = packet[DNSQR].qname.decode('utf-8')
        if 'pes21-pc.konamionline.com' in qname:
            dns_resp = IP(dst=packet[IP].src) / \
                      UDP(dport=packet[UDP].sport, sport=53) / \
                      DNS(
                          id=packet[DNS].id,
                          qr=1,  # Response
                          aa=1,  # Authoritative
                          rd=1,  # Recursion Desired
                          ra=1,  # Recursion Available
                          qd=packet[DNS].qd,
                          an=DNSRR(
                              rrname=packet[DNSQR].qname,
                              type='A',
                              ttl=60,
                              rdata='127.0.0.1'  # Point to local server
                          )
                      )
            return dns_resp
    return None

def create_upnp_response(packet):
    """Create response for UPnP/SSDP discovery"""
    if packet.haslayer(Raw) and b'M-SEARCH' in packet[Raw].load:
        response = IP(dst=packet[IP].src) / \
                  UDP(sport=1900, dport=packet[UDP].sport) / \
                  "HTTP/1.1 200 OK\r\n" \
                  "ST: urn:schemas-upnp-org:device:InternetGatewayDevice:1\r\n" \
                  "USN: uuid:PES-SERVER-1\r\n" \
                  "Location: http://127.0.0.1:2869/upnphost/udhisapi.dll\r\n" \
                  "Cache-Control: max-age=1800\r\n" \
                  "Server: PES/1.0 UPnP/1.0\r\n" \
                  "EXT:\r\n\r\n"
        return response
    return None

def create_tcp_response(packet):
    """Create appropriate TCP response"""
    if packet.haslayer(TCP):
        flags = "SA" if packet[TCP].flags & 0x02 else "A"  # SYN-ACK for SYN, ACK for others
        
        response = IP(dst=packet[IP].src, src=packet[IP].dst) / \
                  TCP(
                      sport=packet[TCP].dport,
                      dport=packet[TCP].sport,
                      seq=packet[TCP].ack if packet[TCP].ack else 0,
                      ack=packet[TCP].seq + 1 if packet[TCP].flags & 0x02 else packet[TCP].seq,
                      flags=flags
                  )

        # Add TLS response if needed
        if packet.haslayer(Raw) and packet[Raw].load.hex().startswith('1703'):
            response /= Raw(load=bytes.fromhex('170303'))
        
        return response
    return None

def handle_packet(packet):
    """Handle incoming packets and generate appropriate responses"""
    try:
        if not packet.haslayer(IP):
            return

        src_ip = packet[IP].src
        dst_ip = packet[IP].dst
        
        # Handle DNS queries
        if packet.haslayer(DNS):
            response = create_dns_response(packet)
            if response:
                send(response, verbose=False)
                logging.info(f"Sent DNS response to {src_ip}")
                return

        # Handle UPnP/SSDP discovery
        if packet.haslayer(UDP) and packet.haslayer(Raw):
            response = create_upnp_response(packet)
            if response:
                send(response, verbose=False)
                logging.info(f"Sent UPnP response to {src_ip}")
                return

        # Handle TCP connections
        if packet.haslayer(TCP):
            response = create_tcp_response(packet)
            if response:
                send(response, verbose=False)
                logging.info(f"Sent TCP response to {src_ip}")
                return

    except Exception as e:
        logging.error(f"Error handling packet: {str(e)}")
        print(f"Error handling packet: {str(e)}")

def start_emulator():
    print("Starting PES Emulator...")
    logging.info("Starting PES Emulator...")
    sniff(filter="tcp or udp", prn=handle_packet, store=0)

if __name__ == "__main__":
    start_emulator()
