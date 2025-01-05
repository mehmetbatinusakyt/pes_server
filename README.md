# PES 2021 Team Play Lobby Server

## Project Overview

### English
PES 2021 Team Play Lobby Server is a custom server implementation that emulates Konami's original 11v11 match functionality. Provides full control over matchmaking, lobbies, and server configuration.

### Български
PES 2021 Team Play Lobby Server е персонализирана сървърна имплементация, която емулира оригиналната функционалност на Konami сървъра за 11v11 мачове. Осигурява пълен контрол върху matchmaking, лобита и конфигурация на сървъра.

---

## File Structure

```bash
pes_server/
├── core/                  # Core server components
│   ├── server.py          # Main server implementation
│   ├── server_emulator.py # Server emulation logic
│   ├── game_server.py     # Team Play Lobby implementation
│   └── network_manager.py # Network communication handler
├── auth/                  # Authentication system
│   ├── auth_server.py     # Authentication server
│   └── wp_login.py        # WordPress integration
├── game/                  # Game management
│   ├── lobby_manager.py   # Lobby creation/management
│   ├── match_manager.py   # Match coordination
│   └── team_manager.py    # Team management
├── network/               # Network infrastructure
│   ├── dns_server.py      # Custom DNS server
│   ├── stun_server.py     # NAT traversal
│   └── packet_decoder.py  # Packet analysis
├── launcher/              # Client launcher
│   ├── pes_launcher.py    # Main launcher
│   └── user_interface.py  # Launcher UI
├── config/                # Configuration files
│   ├── config.py          # Server settings
│   └── hosts.py           # DNS mappings
├── logs/                  # Log files
└── certs/                 # SSL certificates
```

---

## Key Components

### WordPress Integration (wp_login.py)

#### English
- User authentication through WordPress user database
- Password validation (supports both MD5 and phpass hashes)
- Connection to WordPress MySQL database
- Logging of all operations

#### Български
- Автентикация на потребители чрез WordPress потребителската база
- Валидация на пароли (поддържа както MD5, така и phpass хешове)
- Връзка с MySQL базата данни на WordPress
- Логиране на всички операции

**Configuration (config.py):**
- wp_db_host: Database host
- wp_db_user: Database username
- wp_db_password: Database password
- wp_db_name: Database name
- wp_db_port: Database port

---

### Game Server (game_server.py)

#### English
- Manages connections between players
- Coordinates lobby creation and management
- Handles client messaging
- Maintains match state
- Integrates with WordPress for user authentication

#### Български
- Управлява връзките между играчите
- Координира създаването и управлението на лобита
- Обработва съобщения между клиентите
- Поддържа състоянието на мача
- Интегрира се с WordPress за потребителска автентикация

---

## Server Configuration

### Basic Setup
1. Edit `config.py` with your server settings
2. Configure DNS mappings in `hosts.py`
3. Place SSL certificates in `certs/` directory
4. Set up WordPress integration in `wp_login.py`

### STUN Server Configuration
- STUN_SERVER_IP: Your public IP address
- STUN_SERVER_PORT: Default 3478
- STUN_LOG_LEVEL: Debug level (1-3)

---

## Startup Sequence

1. Start STUN server: `python stun_server.py`
2. Start DNS server: `python dns_server.py`
3. Start main server: `python server.py`
4. Launch the client: `python pes_launcher.py`
5. Access admin panel: `http://localhost:8000/admin`

---

## Additional Notes

- Ensure all services are running before starting the client
- Monitor logs in the `logs/` directory for troubleshooting
- Regularly back up configuration files
- Use the admin panel for server management and monitoring
