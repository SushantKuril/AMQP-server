#!/bin/bash

# Set resource limits
sudo rabbitmqctl set_vm_memory_high_watermark 0.7
sudo rabbitmqctl set_disk_free_limit "2GB"

# Set policy for queue length limits
sudo rabbitmqctl set_policy queue-limits \
    ".*" \
    '{"max-length": 10000, "max-length-bytes": 104857600}' \
    --apply-to queues

# Set connection and channel limits
sudo rabbitmqctl set_user_tags myapp monitoring
sudo rabbitmqctl set_user_limits myapp '{"max-connections": 100, "max-channels": 10}'

# Enable consumer acknowledgement timeout
sudo rabbitmqctl set_policy ack-timeout \
    ".*" \
    '{"consumer-timeout": 1800000}' \
    --apply-to queues

# Enable message TTL (Time To Live)
sudo rabbitmqctl set_policy message-ttl \
    ".*" \
    '{"message-ttl": 3600000}' \
    --apply-to queues

echo "Defense configuration applied successfully"
