# WordPress Configuration
WORDPRESS_CONFIG = {
    'url': 'http://localhost',  # WordPress site URL
    'db_host': 'localhost',     # Database host
    'db_user': 'wp',            # Database user
    'db_password': 'wp',        # Database password
    'db_name': 'wp',            # Database name
}

# Server Configuration
SERVER_CONFIG = {
    'host': '0.0.0.0',          # Server host
    'port': 5739,               # Server port
    'max_players': 22,          # Maximum players per match
    'positions': [              # Available positions
        'GK', 'LB', 'CB1', 'CB2', 'RB',
        'LM', 'CM1', 'CM2', 'RM',
        'CF1', 'CF2'
    ]
}

# Network Configuration
NETWORK_CONFIG = {
    'ssl': {
        'enabled': True,
        'certfile': 'certs/server.crt',
        'keyfile': 'certs/server.key'
    },
    'stun_servers': [
        {'host': 'stun1.l.google.com', 'port': 19302},
        {'host': 'stun2.l.google.com', 'port': 19302}
    ],
    'turn_servers': [
        {
            'host': 'turn1.peslobby.com',
            'port': 3478,
            'username': 'pes_lobby_user',
            'password': 'TURNp@ssw0rd!2024'
        },
        {
            'host': 'turn2.peslobby.com',
            'port': 3478,
            'username': 'pes_lobby_user',
            'password': 'TURNp@ssw0rd!2024'
        },
        {
            'host': 'turn3.peslobby.com',
            'port': 3478,
            'username': 'pes_lobby_user',
            'password': 'TURNp@ssw0rd!2024'
        }
    ]
}

# Database Configuration
DATABASE_CONFIG = {
    'host': 'localhost',
    'user': 'wp',
    'password': 'wp',
    'database': 'wp',
    'pool_size': 20,
    'charset': 'utf8mb4',
    'autocommit': True,
    'connect_timeout': 10
}
