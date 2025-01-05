import socket
import dns.resolver
import dns.message
import dns.query
import logging
from datetime import datetime
from dnslib import DNSRecord, QTYPE, RR, A, AAAA
from dnslib.server import DNSServer
import threading
import time

class LocalDNS:
    def __init__(self, target_ip, upstream_dns='8.8.8.8'):
        self.target_ip = target_ip
        self.upstream_dns = upstream_dns
        self.query_count = 0
        self.start_time = time.time()
        self.lock = threading.Lock()
        
        # Ensure logs directory exists
        import os
        os.makedirs('logs', exist_ok=True)
        
        # Setup logging with detailed startup info
        log_filename = f"logs/dns_tracker_{datetime.now().strftime('%Y-%m-%d')}.log"
        logging.basicConfig(
            filename=log_filename,
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Print startup information
        print(f"Starting DNS server with target IP: {self.target_ip}")
        print(f"Logging to: {log_filename}")
        logging.info(f"Starting DNS server with target IP: {self.target_ip}")

    def forward_query(self, query):
        """Forward DNS query to upstream DNS using dnspython"""
        domain = str(query.q.qname).rstrip('.')  # Remove trailing dot
        qtype = dns.rdatatype.to_text(query.q.qtype)
        
        # Rate limiting
        with self.lock:
            self.query_count += 1
            if self.query_count > 1000 and (time.time() - self.start_time) < 60:
                logging.warning(f"Rate limit exceeded for {domain}")
                return None
        
        logging.info(f"Forwarding {domain} (type {qtype}) to upstream DNS")
        
        # Skip reverse DNS lookups
        if domain.endswith('.in-addr.arpa') or domain.endswith('.ip6.arpa'):
            return None
            
        try:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = [self.upstream_dns]
            
            response = resolver.resolve(domain, qtype)
            
            reply = DNSRecord(q=query.q)
            for rdata in response:
                if qtype == 'A':
                    reply.add_answer(RR(domain, QTYPE.A, rdata=A(str(rdata))))
                elif qtype == 'AAAA':
                    reply.add_answer(RR(domain, QTYPE.AAAA, rdata=AAAA(str(rdata))))
            
            logging.info(f"Received response for {domain}: {reply}")
            return reply
            
        except Exception as e:
            logging.error(f"Error while resolving {domain}: {str(e)}", exc_info=True)
            return None

    def resolve(self, request, handler):
        reply = request.reply()
        qname = request.q.qname
        qtype = request.q.qtype
        client_ip = handler.client_address[0]

        # Log all DNS queries
        logging.info(f"DNS query from {client_ip} for {qname} (type {QTYPE[qtype]})")
        print(f"Received DNS query from {client_ip} for {qname} (type {QTYPE[qtype]})")

        # Intercept PES-related domains
        pes_domains = [
            'konami-server.com.',
            'cs.konami.net.',
            'ntl.service.konami.net.',
            'ntleu.service.konami.net.',
            'pes-teamplay.com.',
            'pes21-x64-stun.cs.konami.net:5740',
            'pes21-x64-gate.cs.konami.net:5739'
        ]
        
        if any(str(qname).endswith(domain) for domain in pes_domains):
            logging.info(f"Redirecting {qname} to {self.target_ip}")
            print(f"Intercepting {qname} query, responding with {self.target_ip}")
            reply.add_answer(RR(qname, QTYPE.A, rdata=A(self.target_ip)))
            return reply
        
        # Forward all other queries
        logging.info(f"Forwarding {qname} to upstream DNS")
        response = self.forward_query(request)
        return response if response else request.reply()

def run_dns_server(target_ip='127.0.0.1', port=53):
    resolver = LocalDNS(target_ip)
    server = DNSServer(resolver, port=port, address='0.0.0.0')
    print(f"DNS server running on all interfaces:{port}, redirecting cs.konami.net to {target_ip}")
    logging.info(f"DNS server bound to 0.0.0.0:{port}")
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down DNS server...")
        logging.info("DNS server shutdown")
    except Exception as e:
        logging.error(f"Failed to start DNS server: {str(e)}")
        print(f"Error starting DNS server: {str(e)}")
    finally:
        server.stop()

if __name__ == '__main__':
    run_dns_server()
