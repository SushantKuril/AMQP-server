#!/bin/bash

# Activate virtual environment if it exists, create if it doesn't
if [ ! -d "venv" ]; then
    python3 -m venv venv
    source venv/bin/activate
    pip install pika
else
    source venv/bin/activate
fi

# Run the consumer script
python consumer.py
