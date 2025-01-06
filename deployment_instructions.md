# Deployment Instructions

## 1. Required Files for Each Device

### Publisher Device Needs:
```
├── publisher.py
├── config.py
├── connection_helper.py
├── run_publisher.sh
└── requirements.txt
```

### Consumer Device Needs:
```
├── consumer.py
├── config.py
├── connection_helper.py
├── run_consumer.sh
└── requirements.txt
```

## 2. Setup Steps for Each Device

1. Install Python 3 if not already installed:
   ```bash
   sudo apt-get update
   sudo apt-get install python3 python3-pip
   ```

2. Create a new directory and copy the required files:
   ```bash
   mkdir rabbitmq_client
   cd rabbitmq_client
   # Copy the required files here
   ```

3. Make the run scripts executable:
   ```bash
   chmod +x run_publisher.sh  # For publisher device
   chmod +x run_consumer.sh   # For consumer device
   ```

## 3. Configuration

Edit `config.py` on each device to point to your RabbitMQ server:
```python
RABBITMQ_CONFIG = {
    'host': 'YOUR_RABBITMQ_SERVER_IP',  # Change this
    # ... rest of the config remains the same
}
```

## 4. Running the Scripts

### On Publisher Device:
```bash
./run_publisher.sh
```

### On Consumer Device:
```bash
./run_consumer.sh
```

## 5. Monitoring

1. Check logs in the same directory:
   ```bash
   tail -f amqp_operations.log
   ```

2. Access RabbitMQ management interface:
   ```
   http://YOUR_RABBITMQ_SERVER_IP:15672
   ```

## 6. Troubleshooting

1. Connection Issues:
   ```bash
   # Test network connectivity
   ping YOUR_RABBITMQ_SERVER_IP
   
   # Test port accessibility
   nc -zv YOUR_RABBITMQ_SERVER_IP 5672
   ```

2. Permission Issues:
   ```bash
   # Check file permissions
   ls -l run_*.sh
   
   # Fix permissions if needed
   chmod +x run_*.sh
   ```

3. Common Error Solutions:
   - Connection refused: Check if RabbitMQ is running on the server
   - Authentication failed: Verify credentials in config.py
   - Permission denied: Check user permissions in RabbitMQ
