import pika
import json
import logging
import time
from typing import Dict, Any
from datetime import datetime, UTC
from config import RABBITMQ_CONFIG, RETRY_CONFIG

logger = logging.getLogger(__name__)

class MessageConsumer:
    def __init__(self):
        self.config = RABBITMQ_CONFIG
        self.connect()
        self.processed_count = 0

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
                
                # Declare exchange
                self.channel.exchange_declare(
                    exchange=self.config['exchange_name'],
                    exchange_type='direct',
                    durable=True
                )
                
                # Declare queue
                self.channel.queue_declare(
                    queue=self.config['queue_name'],
                    durable=True
                )
                
                # Bind queue to exchange
                self.channel.queue_bind(
                    exchange=self.config['exchange_name'],
                    queue=self.config['queue_name'],
                    routing_key=self.config['routing_key']
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
        """Process the received message with enhanced logging."""
        try:
            order_data = message['data']
            order_id = order_data.get('order_id', 'unknown')
            status = order_data.get('status', 'unknown')
            priority = order_data.get('priority', 'unknown')
            total_amount = order_data.get('total_amount', 0)
            
            logger.info(f"Processing order: {order_id}")
            logger.info(f"Order details: Status={status}, Priority={priority}, Amount=${total_amount}")
            
            # Simulate processing based on priority
            if priority == 'high':
                time.sleep(0.5)
            elif priority == 'medium':
                time.sleep(1)
            else:
                time.sleep(1.5)
                
            self.processed_count += 1
            logger.info(f"Order {order_id} processed successfully. Total processed: {self.processed_count}")
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            raise

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
        """Start consuming messages with enhanced error handling."""
        try:
            # Set QoS
            self.channel.basic_qos(prefetch_count=1)
            
            # Setup consumer
            self.channel.basic_consume(
                queue=self.config['queue_name'],
                on_message_callback=self.callback
            )
            
            logger.info(f"Started consuming from queue: {self.config['queue_name']}")
            logger.info("Press CTRL+C to exit")
            
            self.channel.start_consuming()
            
        except KeyboardInterrupt:
            logger.info(f"Shutting down consumer. Total messages processed: {self.processed_count}")
            self.channel.stop_consuming()
        except Exception as e:
            logger.error(f"Error in consumer: {str(e)}")
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
