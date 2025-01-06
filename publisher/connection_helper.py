import pika
import time
import logging
from typing import Tuple
from config import RABBITMQ_CONFIG, RETRY_CONFIG

logger = logging.getLogger(__name__)

def create_connection() -> Tuple[pika.BlockingConnection, pika.channel.Channel]:
    """Create a connection to RabbitMQ with error handling."""
    credentials = pika.PlainCredentials(
        RABBITMQ_CONFIG['credentials']['username'],
        RABBITMQ_CONFIG['credentials']['password']
    )
    
    connection = None
    channel = None
    
    for attempt in range(RETRY_CONFIG['max_retries']):
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_CONFIG['host'],
                    port=RABBITMQ_CONFIG['port'],
                    virtual_host=RABBITMQ_CONFIG['virtual_host'],
                    credentials=credentials,
                    heartbeat=600,
                    connection_attempts=3,
                    retry_delay=2
                )
            )
            channel = connection.channel()
            
            # Declare exchange and queue
            channel.exchange_declare(
                exchange=RABBITMQ_CONFIG['exchange_name'],
                exchange_type='direct',
                durable=True
            )
            
            channel.queue_declare(
                queue=RABBITMQ_CONFIG['queue_name'],
                durable=True
            )
            
            channel.queue_bind(
                exchange=RABBITMQ_CONFIG['exchange_name'],
                queue=RABBITMQ_CONFIG['queue_name'],
                routing_key=RABBITMQ_CONFIG['routing_key']
            )
            
            logger.info("Successfully connected to RabbitMQ")
            return connection, channel
            
        except pika.exceptions.AMQPConnectionError as e:
            error_msg = str(e).lower()
            if 'authentication failed' in error_msg:
                logger.error(RETRY_CONFIG['error_messages']['auth_failed'])
            elif 'connection refused' in error_msg:
                logger.error(RETRY_CONFIG['error_messages']['connection_refused'])
            else:
                logger.error(f"{RETRY_CONFIG['error_messages']['unknown']} Error: {str(e)}")
            
            if attempt + 1 < RETRY_CONFIG['max_retries']:
                time.sleep(RETRY_CONFIG['retry_delay'])
            else:
                raise Exception("Failed to connect to RabbitMQ after multiple attempts")
    
    return None, None
