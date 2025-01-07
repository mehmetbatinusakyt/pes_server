# PES 2021 Team Play Lobby Server

## Project Overview

### English
It's not working, it is still in development!
PES 2021 Team Play Lobby Server is a custom server implementation that emulates Konami's original 11v11 match functionality. Provides full control over matchmaking, lobbies, and server configuration.
We still have no success with connecting the game to the server, but I hope that will change.

### Български

PES 2021 Team Play Lobby Server е персонализирана сървърна имплементация, която емулира оригиналната функционалност на Konami сървъра за 11v11 мачове. Осигурява пълен контрол върху matchmaking, лобита и конфигурация на сървъра.
Все още нямаме успех с това да вържем играта към сървъра, но се надявам това да се промени.
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

## Server Architecture and Startup

### Component Integration

- `server.py` is the main entry point that manages all components
- It imports and uses:
  - `wp_login.py` for WordPress authentication
  - `game_server.py` for Team Play Lobby functionality
  - `network_manager.py` for network operations
- Other components are started as separate processes

### Detailed Startup Sequence

1. Start STUN server (required for NAT traversal):

   ```bash
   python stun_server.py
   ```

2. Start DNS server (handles custom domain resolution):

   ```bash
   python dns_server.py
   ```

3. Start main server (manages all game and authentication services):

   ```bash
   python server.py
   ```

   - Automatically loads:
     - WordPress authentication (wp_login.py)
     - Game server (game_server.py)
     - Network manager
     - Lobby manager

4. Launch the client application:

   ```bash
   python pes_launcher.py
   ```

5. Access admin panel:

   ```bash
   http://localhost:8000/admin
   ```

### Component Dependencies

```mermaid
graph TD
    A[server.py] --> B[wp_login.py]
    A --> C[game_server.py]
    A --> D[network_manager.py]
    C --> E[lobby_manager.py]
    C --> F[match_manager.py]
    B --> G[WordPress DB]

---

## Additional Notes

- Ensure all services are running before starting the client
- Monitor logs in the `logs/` directory for troubleshooting
- Regularly back up configuration files
- Use the admin panel for server management and monitoring

## Change History

For detailed information about project changes and updates, see [CHANGELOG.md](CHANGELOG.md)
