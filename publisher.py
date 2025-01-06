import pika
import json
import time
import random
import logging
from datetime import datetime, UTC
from typing import Dict, Any
from config import RABBITMQ_CONFIG, RETRY_CONFIG

logger = logging.getLogger(__name__)

class MessagePublisher:
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
                
                # Declare exchange before queue
                self.channel.exchange_declare(
                    exchange=self.config['exchange_name'],
                    exchange_type='direct',
                    durable=True
                )
                
                # Declare queue and bind to exchange
                self.channel.queue_declare(
                    queue=self.config['queue_name'],
                    durable=True
                )
                
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

    def publish_message(self, message_data: Dict[str, Any]) -> None:
        try:
            message = {
                'timestamp': datetime.now(UTC).isoformat(),  # Updated to use timezone-aware datetime
                'data': message_data,
                'message_id': int(time.time() * 1000),
                'source': 'production_system'
            }
            
            self.channel.basic_publish(
                exchange=self.config['exchange_name'],
                routing_key=self.config['routing_key'],
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                    content_type='application/json',
                    content_encoding='utf-8'
                )
            )
            logger.info(f"Published message {message['message_id']}")
        except Exception as e:
            logger.error(f"Error publishing message: {str(e)}")
            raise

    def generate_random_order(self) -> Dict[str, Any]:
        """Generate a random order message."""
        products = [
            {'id': 'PROD123', 'name': 'Laptop', 'price': 999.99},
            {'id': 'PROD456', 'name': 'Smartphone', 'price': 499.99},
            {'id': 'PROD789', 'name': 'Headphones', 'price': 99.99},
            {'id': 'PROD012', 'name': 'Monitor', 'price': 299.99},
            {'id': 'PROD345', 'name': 'Keyboard', 'price': 79.99}
        ]
        
        # Select random products and quantities
        order_items = []
        num_items = random.randint(1, 3)
        selected_products = random.sample(products, num_items)
        
        total_amount = 0
        for product in selected_products:
            quantity = random.randint(1, 5)
            item_total = product['price'] * quantity
            total_amount += item_total
            
            order_items.append({
                'product_id': product['id'],
                'product_name': product['name'],
                'quantity': quantity,
                'price': product['price'],
                'item_total': item_total
            })

        # Generate random customer data
        customer_id = f'CUST{random.randint(1000, 9999)}'
        
        return {
            'order_id': f'ORD{int(time.time() * 1000)}',
            'customer': {
                'id': customer_id,
                'name': f'Customer {customer_id}',
                'email': f'customer{customer_id.lower()}@example.com'
            },
            'items': order_items,
            'total_amount': round(total_amount, 2),
            'shipping_address': {
                'street': f'{random.randint(1, 999)} Main St',
                'city': random.choice(['Boston', 'New York', 'Chicago', 'San Francisco']),
                'state': random.choice(['MA', 'NY', 'IL', 'CA']),
                'zip': f'{random.randint(10000, 99999)}'
            },
            'status': random.choice(['pending', 'processing', 'shipped']),
            'priority': random.choice(['low', 'medium', 'high'])
        }

    def run_continuous_publishing(self, interval: float = 1.0):
        """Continuously publish random messages with specified interval."""
        try:
            logger.info("Started continuous message publishing. Press Ctrl+C to stop.")
            message_count = 0
            while True:
                order_data = self.generate_random_order()
                self.publish_message(order_data)
                message_count += 1
                logger.info(f"Total messages published: {message_count}")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info(f"Stopping publisher. Total messages sent: {message_count}")
        except Exception as e:
            logger.error(f"Error in continuous publishing: {str(e)}")
        finally:
            self.close()

    def close(self) -> None:
        if self.connection and not self.connection.is_closed:
            self.connection.close()

if __name__ == "__main__":
    publisher = MessagePublisher()
    # Set the interval between messages (in seconds)
    publishing_interval = 2.0  # Adjust this value as needed
    publisher.run_continuous_publishing(publishing_interval)
