# Attack Scripts

## Slow DoS Attack Script

- Creates multiple persistent connections  
- Sends messages character by character with delays  
- Uses large message payloads  
- Maintains connections open for long periods  
- Gradually establishes connections to avoid detection  
- Monitors active connections  
- Implements graceful shutdown  

### Key Features of the Slow DoS Attack

- Multiple slow connections instead of rapid messages  
- Character-by-character transmission to keep connections busy  
- Large payloads to consume memory  
- Random delays between messages  
- Connection monitoring  
- Graceful cleanup on exit  

### To Run the Slow DoS Attack

```bash
python Attack/slow_publisher.py
```

**Note:** This type of attack is particularly effective because it:  
- Consumes server resources over longer periods  
- Is harder to detect than flood attacks  
- Keeps connections open and active  
- Gradually degrades server performance  

---

## Flood Attack Script

- Creates multiple threads to send messages simultaneously  
- Generates random messages with substantial payload  
- Sends messages as fast as possible without any rate limiting  
- Creates separate queues for each thread to maximize impact  
- Tracks and displays message count statistics  

### To Run the Flood Attack

```bash
python Attack/flood_publisher.py
```

The script will create 10 threads by default, each flooding its own queue with messages. You can adjust the number of threads and the host IP address as needed.