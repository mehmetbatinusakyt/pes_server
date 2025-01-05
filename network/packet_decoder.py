import binascii
import json
from datetime import datetime

class PESPacketDecoder:
    def __init__(self):
        self.known_patterns = {
            b'STEAM': 'Steam Client Auth',
            b'PCApp': 'PC Application Data',
            b'TEAMPLAYLOBBY': 'Team Play Lobby Request',
            b'AUTH': 'Authentication Request',
            b'MATCHMAKING': 'Matchmaking Data'
        }
        
    def decode_hex(self, hex_string):
        try:
            return binascii.unhexlify(hex_string.replace(' ', ''))
        except:
            return None
            
    def analyze_packet(self, payload_hex):
        decoded = self.decode_hex(payload_hex)
        if not decoded:
            return "Invalid hex data"
            
        results = {
            'timestamp': datetime.now().isoformat(),
            'size': len(decoded),
            'type': 'Unknown',
            'patterns_found': []
        }
        
        # Check for known patterns
        for pattern, ptype in self.known_patterns.items():
            if pattern in decoded:
                results['patterns_found'].append(ptype)
                results['type'] = ptype
                
        # Check for TLS 1.3 header
        if payload_hex.startswith('1703'):
            results['type'] = 'TLS 1.3 Data'
            
        return results

    def save_analysis(self, results, filename='packet_analysis.json'):
        with open(filename, 'a') as f:
            json.dump(results, f, indent=2)
            f.write('\n')

if __name__ == "__main__":
    decoder = PESPacketDecoder()
    # Test with sample payload
    sample = "1703030022000000000000000000000000000000000000000000000000000000"
    results = decoder.analyze_packet(sample)
    print(json.dumps(results, indent=2))
