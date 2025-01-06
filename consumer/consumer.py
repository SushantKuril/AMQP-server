import pika
import json
import logging
import time
from typing import Dict, Any
from datetime import datetime
from config import RABBITMQ_CONFIG, RETRY_CONFIG

logger = logging.getLogger(__name__)

class MessageConsumer:
    def __init__(self):
        self.config = RABBITMQ_CONFIG
        self.connect()

    def connect(self) -> None:
        credentials = pika.PlainCredentials(
            self.config['credentials']['username'],
            self.config['credentials']['password']
        )
        
        for attempt in range(RETRY_CONFIG['max_retries']):
            try:
                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host=self.config['host'],
                        port=self.config['port'],
                        virtual_host=self.config['virtual_host'],
                        credentials=credentials,
                        heartbeat=600
                    )
                )
                self.channel = self.connection.channel()
                self.channel.queue_declare(
                    queue=self.config['queue_name'],
                    durable=True
                )
                logger.info("Successfully connected to RabbitMQ")
                break
            except Exception as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {str(e)}")
                if attempt + 1 < RETRY_CONFIG['max_retries']:
                    time.sleep(RETRY_CONFIG['retry_delay'])
                else:
                    raise

    def validate_message(self, message: Dict[str, Any]) -> bool:
        required_fields = ['timestamp', 'data', 'message_id', 'source']
        return all(field in message for field in required_fields)

    def process_message(self, message: Dict[str, Any]) -> None:
        # Example processing logic
        if message['data'].get('status') == 'pending':
            # Process the order
            logger.info(f"Processing order {message['data'].get('order_id')}")
            # Simulate some processing time
            time.sleep(1)
            logger.info(f"Order {message['data'].get('order_id')} processed successfully")

    def callback(self, ch, method, properties, body: bytes) -> None:
        try:
            message = json.loads(body.decode())
            logger.info(f"Received message {message.get('message_id')}")
            
            if not self.validate_message(message):
                logger.error("Invalid message format")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return

            self.process_message(message)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding message: {str(e)}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def start_consuming(self) -> None:
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue=self.config['queue_name'],
            on_message_callback=self.callback
        )
        logger.info("Started consuming messages")
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()
        finally:
            self.close()

    def close(self) -> None:
        if self.connection and not self.connection.is_closed:
            self.connection.close()

if __name__ == "__main__":
    consumer = MessageConsumer()
    try:
        consumer.start_consuming()
    except KeyboardInterrupt:
        logger.info("Shutting down consumer")
    finally:
        consumer.close()
