import logging

# RabbitMQ Defense Configuration
DEFENSE_CONFIG = {
    # Queue limits
    'max_queue_length': 10000,  # Maximum number of messages per queue
    'max_queue_size_bytes': 100 * 1024 * 1024,  # 100MB per queue
    
    # Message limits
    'max_message_size': 1024 * 1024,  # 1MB maximum message size
    'rate_limit': {
        'messages_per_second': 100,
        'burst_size': 50
    },
    
    # Connection limits
    'max_connections': 100,
    'max_channels_per_connection': 10,
    
    # Monitoring thresholds
    'alert_thresholds': {
        'queue_length': 5000,
        'message_rate': 50,
        'connection_count': 50
    }
}

# Defensive logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - [%(levelname)s] - %(message)s',
    handlers=[
        logging.FileHandler('defense_operations.log'),
        logging.StreamHandler()
    ]
)
