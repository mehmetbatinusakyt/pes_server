import re
from collections import defaultdict

class PESLogAnalyzer:
    def __init__(self):
        self.connections = defaultdict(list)
        self.main_server = "18.165.61.88"
        self.game_server = "40.86.103.106"
        self.tls_packets = []
        
    def analyze_log_file(self, filename):
        print("=== PES Connection Analysis ===\n")
        
        with open(filename, 'r') as f:
            for line in f:
                print(f"Analyzing line: {line.strip()}")  # Добавяме лог за всяка линия
                # Анализ на TLS пакети (1703 header)
                if 'Payload: 1703' in line:
                    payload = line.split('Payload: ')[1].strip()
                    self.tls_packets.append(payload)
                
                # Анализ на връзките
                if 'Connection attempt:' in line:
                    src, dst = self._extract_connection_info(line)
                    if src and dst:
                        self.connections[src].append(dst)
        
        self._print_analysis()
    
    def _extract_connection_info(self, line):
        pattern = r"(\d+\.\d+\.\d+\.\d+)\s*->\s*(\d+\.\d+\.\d+\.\d+)"
        match = re.search(pattern, line)
        if match:
            return match.group(1), match.group(2)
        return None, None
    
    def _print_analysis(self):
        print("Connection Flow:")
        print(f"1. Initial Auth Server: {self.main_server}")
        auth_connections = len([x for x in self.connections[self.main_server]])
        print(f"   - Authentication attempts: {auth_connections}")
        
        print(f"\n2. Game Server: {self.game_server}")
        game_connections = len([x for x in self.connections[self.game_server]])
        print(f"   - Game server connections: {game_connections}")
        
        print("\nTLS Analysis:")
        print(f"- Total TLS packets: {len(self.tls_packets)}")
        print("- TLS version: 1.3 (0x1703)")
        
        print("\nConnection Sequence:")
        for src, dsts in self.connections.items():
            print(f"\nFrom {src}:")
            for dst in dsts:
                print(f"  -> {dst}")
        
        self._save_findings()
    
    def _save_findings(self):
        try:
            with open('connection_analysis.txt', 'w') as f:
                f.write("=== PES Server Emulation Requirements ===\n\n")
                f.write(f"1. Main Authentication Server: {self.main_server}\n")
                f.write("   - Requires TLS 1.3 support\n")
                f.write("   - Handles initial connection\n\n")
                f.write(f"2. Game Server: {self.game_server}\n")
                f.write("   - Handles actual game communication\n")
                f.write("   - Receives redirected connections\n\n")
                f.write("3. Protocol Details:\n")
                f.write("   - Uses TLS 1.3 encryption\n")
                f.write("   - Initial handshake required\n")
                f.write("   - Multiple connection sequence\n")
            print("Analysis saved to connection_analysis.txt")
        except Exception as e:
            print(f"Error saving analysis: {e}")

if __name__ == "__main__":
    analyzer = PESLogAnalyzer()
    analyzer.analyze_log_file("pes_lobby_connections.log")
