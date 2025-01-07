import logging

# RabbitMQ Configuration
RABBITMQ_CONFIG = {
    'host': '64.227.154.108',
    'port': 5672,
    'virtual_host': '/',
    'credentials': {
        'username': 'myapp',  # Updated username
        'password': 'mypassword'  # Updated password
    },
    'queue_name': 'production_queue',
    'exchange_name': 'main_exchange',
    'routing_key': 'production_route'
}

# Retry Configuration
RETRY_CONFIG = {
    'max_retries': 5,  # Increased retries
    'retry_delay': 5,  # seconds
    'error_messages': {
        'auth_failed': 'Authentication failed. Please check username and password.',
        'connection_refused': 'Connection refused. Please check if RabbitMQ server is running.',
        'unknown': 'An unknown error occurred while connecting to RabbitMQ.'
    }
}

# Setup logging with more detailed formatting
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - [%(levelname)s] - %(message)s',
    handlers=[
        logging.FileHandler('amqp_operations.log'),
        logging.StreamHandler()
    ]
)

# Add log level for connection issues
logging.getLogger('pika').setLevel(logging.WARNING)
