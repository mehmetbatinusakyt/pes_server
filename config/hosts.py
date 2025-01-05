import os
import sys
import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def modify_hosts():
    if not is_admin():
        print("This script needs admin rights!")
        sys.exit(1)

    hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
    hosts_entries = [
        "127.0.0.1 pes21-pc.konamionline.com",
        "127.0.0.1 18.165.61.88",
        "127.0.0.1 40.86.103.106",
        "127.0.0.1 konami-server.com",
        "127.0.0.1 cs.konami.net",
        "127.0.0.1 ntl.service.konami.net",
        "127.0.0.1 ntleu.service.konami.net",
        "127.0.0.1 pes-teamplay.com"
    ]
    
    print("Adding PES server redirects to hosts file...")
    
    try:
        with open(hosts_path, 'r+') as f:
            content = f.read()
            for entry in hosts_entries:
                if entry not in content:
                    f.write(f"\n{entry}")
        print("Hosts file updated successfully!")
    except Exception as e:
        print(f"Error updating hosts file: {e}")

if __name__ == "__main__":
    modify_hosts()
