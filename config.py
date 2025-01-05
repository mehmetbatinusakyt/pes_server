# Database configuration
DATABASE_CONFIG = {
    'db_host': 'localhost',
    'db_user': 'wp',
    'db_password': 'wp',
    'db_name': 'wp'
}

# Server configuration
SERVER_CONFIG = {
    'host': '127.0.0.1',
    'udp_port1': 50000,
    'udp_port2': 50001,
    'tcp_port': 5739,
    'proxy_port': 5740,
    'max_players': 22,
    'positions': [
        'GK', 'LB', 'CB1', 'CB2', 'RB',
        'LM', 'CM1', 'CM2', 'RM',
        'ST1', 'ST2'
    ]
}

# Network configuration
NETWORK_CONFIG = {
    'ssl': {
        'enabled': False,
        'certfile': 'certs/server.crt',
        'keyfile': 'certs/server.key'
    },
    'stun_servers': [
        'stun1.l.google.com:19302',
        'stun2.l.google.com:19302'
    ],
    'dns_servers': [
        '8.8.8.8',
        '8.8.4.4'
    ]
}

# WordPress integration
WORDPRESS_CONFIG = {
    'wp_auth_enabled': True,
    'wp_session_timeout': 3600,
    'wp_login_url': 'http://localhost/wp-login.php',
    'wp_admin_url': 'http://localhost/wp-admin/',
    'wp_plugin_dir': 'C:/xampp/htdocs/wp-content/plugins/pes-server-admin'
}
