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

Configuration
Edit config.py with your server settings
Configure DNS mappings in hosts.py
Place SSL certificates in certs/ directory
Set up WordPress integration in wp_login.py

## WordPress Integration (wp_login.py)

### На Български:
wp_login.py е модул за интеграция с WordPress базата данни, който позволява:
- Автентикация на потребители чрез WordPress потребителската база
- Валидация на пароли (поддържа както MD5, така и phpass хешове)
- Връзка с MySQL базата данни на WordPress
- Логиране на всички операции

Модулът използва следната конфигурация от config.py:
- wp_db_host: Хост на базата данни
- wp_db_user: Потребителско име
- wp_db_password: Парола
- wp_db_name: Име на базата данни
- wp_db_port: Порт за връзка

### In English:
wp_login.py is a WordPress database integration module that provides:
- User authentication through WordPress user database
- Password validation (supports both MD5 and phpass hashes)
- Connection to WordPress MySQL database
- Logging of all operations

The module uses the following configuration from config.py:
- wp_db_host: Database host
- wp_db_user: Database username
- wp_db_password: Database password
- wp_db_name: Database name
- wp_db_port: Database port

## Game Server (game_server.py)

### На Български:
game_server.py е основният сървър за Team Play Lobby (11 vs 11) режим, който:
- Управлява връзките между играчите
- Координира създаването и управлението на лобита
- Обработва съобщения между клиентите
- Поддържа състоянието на мача
- Интегрира се с WordPress за потребителска автентикация

### In English:
game_server.py is the main server for Team Play Lobby (11 vs 11) mode that:
- Manages connections between players
- Coordinates lobby creation and management
- Handles client messaging
- Maintains match state
- Integrates with WordPress for user authentication

Server Startup Sequence
Start STUN server: python stun_server.py
Start DNS server: python dns_server.py
Start main server: python server.py
Launch the client: python pes_launcher.py
Access admin panel: http://localhost:8000/admin

STUN Server Configuration
The STUN server is crucial for NAT traversal and must be started first. It runs on port 3478 by default. Configuration options:

STUN_SERVER_IP: Your public IP address
STUN_SERVER_PORT: Default 3478
STUN_LOG_LEVEL: Debug level (1-3)

Българска Версия
Преглед
PES 2021 Team Play Lobby Server е персонализирана сървърна имплементация, която емулира оригиналната функционалност на Konami сървъра за 11v11 мачове. Осигурява пълен контрол върху matchmaking, лобита и конфигурация на сървъра.

Файлова структура
pes_server/
├── core/                  # Основни компоненти
│   ├── server.py          # Основна имплементация
│   ├── server_emulator.py # Емулационна логика
│   ├── game_server.py     # Team Play Lobby имплементация
│   └── network_manager.py # Мрежова комуникация
├── auth/                  # Система за автентикация
│   ├── auth_server.py     # Сървър за автентикация
│   └── wp_login.py        # WordPress интеграция
├── game/                  # Управление на играта
│   ├── lobby_manager.py   # Създаване/управление на лобита
│   ├── match_manager.py   # Координация на мачове
│   └── team_manager.py    # Управление на отбори
├── network/               # Мрежова инфраструктура
│   ├── dns_server.py      # Персонализиран DNS сървър
│   ├── stun_server.py     # NAT traversal
│   └── packet_decoder.py  # Анализ на пакети
├── launcher/              # Клиентски лаунчър
│   ├── pes_launcher.py    # Основен лаунчър
│   └── user_interface.py  # Лаунчър интерфейс
├── config/                # Конфигурационни файлове
│   ├── config.py          # Настройки на сървъра
│   └── hosts.py           # DNS mappings
├── logs/                  # Лог файлове
└── certs/                 # SSL сертификати

Конфигурация
Редактирайте config.py с вашите настройки
Конфигурирайте DNS mappings в hosts.py
Поставете SSL сертификати в certs/ директория
Настройте WordPress интеграция в wp_login.py

Последователност на стартиране
Стартирайте STUN сървър: python stun_server.py
Стартирайте DNS сървър: python dns_server.py
Стартирайте основния сървър: python server.py
Пуснете клиента: python pes_launcher.py
Достап до админ панел: http://localhost:8000/admin

Конфигурация на STUN сървър
STUN сървърът е от съществено значение за NAT traversal и трябва да бъде стартиран първи. Работи на порт 3478 по подразбиране. Настройки:

STUN_SERVER_IP: Вашият публичен IP адрес
STUN_SERVER_PORT: По подразбиране 3478
STUN_LOG_LEVEL: Ниво на дебъг (1-3)
