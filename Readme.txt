# PES 2021 Team Play Lobby Server Documentation

## English Version

### Overview
The PES 2021 Team Play Lobby Server is a custom server implementation that emulates the original Konami server functionality for 11v11 matches. It provides complete control over matchmaking, lobbies, and server configuration.

### File Structure
```
pes_server/
├── core/                  # Core server components
│   ├── server.py          # Main server implementation
│   ├── server_emulator.py # Server emulation logic
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

### Configuration
1. Edit config.py with your server settings
2. Configure DNS mappings in hosts.py
3. Place SSL certificates in certs/ directory
4. Set up WordPress integration in wp_login.py

### Server Startup Sequence
1. Start STUN server: `python stun_server.py`
2. Start DNS server: `python dns_server.py`
3. Start main server: `python server.py`
4. Launch the client: `python pes_launcher.py`
5. Access admin panel: http://localhost:8000/admin

### STUN Server Configuration
The STUN server is crucial for NAT traversal and must be started first. It runs on port 3478 by default. Configuration options:
- STUN_SERVER_IP: Your public IP address
- STUN_SERVER_PORT: Default 3478
- STUN_LOG_LEVEL: Debug level (1-3)

---

## Българска Версия

### Преглед
PES 2021 Team Play Lobby Server е персонализирана сървърна имплементация, която емулира оригиналната функционалност на Konami сървъра за 11v11 мачове. Осигурява пълен контрол върху matchmaking, лобита и конфигурация на сървъра.

### Файлова структура
```
pes_server/
├── core/                  # Основни компоненти
│   ├── server.py          # Основна имплементация
│   ├── server_emulator.py # Емулационна логика
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
```

### Конфигурация
1. Редактирайте config.py с вашите настройки
2. Конфигурирайте DNS mappings в hosts.py
3. Поставете SSL сертификати в certs/ директория
4. Настройте WordPress интеграция в wp_login.py

### Последователност на стартиране
1. Стартирайте STUN сървър: `python stun_server.py`
2. Стартирайте DNS сървър: `python dns_server.py`
3. Стартирайте основния сървър: `python server.py`
4. Пуснете клиента: `python pes_launcher.py`
5. Достап до админ панел: http://localhost:8000/admin

### Конфигурация на STUN сървър
STUN сървърът е от съществено значение за NAT traversal и трябва да бъде стартиран първи. Работи на порт 3478 по подразбиране. Настройки:
- STUN_SERVER_IP: Вашият публичен IP адрес
- STUN_SERVER_PORT: По подразбиране 3478
- STUN_LOG_LEVEL: Ниво на дебъг (1-3)
