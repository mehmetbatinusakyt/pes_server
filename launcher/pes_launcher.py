import os
import sys
import subprocess
import mysql.connector
import time
import psutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configuration
GAME_EXE = "PES2021.exe"
SETTINGS_EXE = "Settings.exe"
SERVER_IP = "127.0.0.1"
SERVER_PORT = 5739

# WordPress Database Configuration
WP_DB_CONFIG = {
    'host': 'localhost',
    'user': 'wp',
    'password': 'wp',
    'database': 'wp'
}

class GameMonitor(FileSystemEventHandler):
    def __init__(self, game_process):
        self.game_process = game_process
        
    def on_modified(self, event):
        if event.src_path.endswith('settings.dat'):
            print("Detected settings change, updating server connection...")
            modify_game_settings()

def connect_to_wordpress():
    try:
        db = mysql.connector.connect(**WP_DB_CONFIG)
        return db
    except mysql.connector.Error as err:
        print(f"WordPress database connection error: {err}")
        return None

def modify_game_settings():
    """Modify game settings to connect to our server"""
    settings_path = os.path.expanduser("~/Documents/KONAMI/eFootball PES 2021 SEASON UPDATE/settings.dat")
    
    try:
        # Create backup
        backup_path = settings_path + ".bak"
        if not os.path.exists(backup_path):
            with open(settings_path, 'rb') as original, open(backup_path, 'wb') as backup:
                backup.write(original.read())
        
        with open(settings_path, 'rb') as f:
            settings = bytearray(f.read())
        
        # Update IP and port
        ip_pattern = b'\x00\x00\x00\x00'
        port_pattern = b'\x00\x00'
        
        ip_index = settings.find(ip_pattern)
        if ip_index != -1:
            settings[ip_index:ip_index+4] = SERVER_IP.encode('utf-8')
            
        port_index = settings.find(port_pattern)
        if port_index != -1:
            settings[port_index:port_index+2] = SERVER_PORT.to_bytes(2, 'little')
            
        with open(settings_path, 'wb') as f:
            f.write(settings)
            
        print("Game settings updated successfully")
        return True
        
    except Exception as e:
        print(f"Error modifying settings: {e}")
        return False

def launch_game():
    """Launch the game executable"""
    try:
        process = subprocess.Popen([GAME_EXE])
        return process
    except Exception as e:
        print(f"Error launching game: {e}")
        return None

def monitor_game(process):
    """Monitor game process and handle crashes"""
    while True:
        retcode = process.poll()
        if retcode is not None:
            print("Game process terminated, attempting to restart...")
            process = launch_game()
            if not process:
                print("Failed to restart game")
                break
        time.sleep(5)

def main():
    # Connect to WordPress
    db = connect_to_wordpress()
    if not db:
        print("Failed to connect to WordPress database")
        sys.exit(1)
        
    # Modify game settings
    if not modify_game_settings():
        print("Failed to modify game settings")
        sys.exit(1)
        
    # Launch game
    game_process = launch_game()
    if not game_process:
        print("Failed to launch game")
        sys.exit(1)
        
    # Start settings watcher
    event_handler = GameMonitor(game_process)
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(os.path.expanduser("~/Documents/KONAMI/eFootball PES 2021 SEASON UPDATE/")))
    observer.start()
    
    try:
        # Monitor game process
        monitor_game(game_process)
    except KeyboardInterrupt:
        observer.stop()
        
    observer.join()

if __name__ == "__main__":
    main()
