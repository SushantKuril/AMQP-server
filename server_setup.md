# RabbitMQ Server Setup

1. **Install RabbitMQ**:
   - On Ubuntu:
     ```sh
     sudo apt-get update
     sudo apt-get install rabbitmq-server
     ```
   - On CentOS:
     ```sh
     sudo yum update
     sudo yum install rabbitmq-server
     ```

2. **Start RabbitMQ Server**:
   ```sh
   sudo systemctl enable rabbitmq-server
   sudo systemctl start rabbitmq-server
   ```

3. **Enable RabbitMQ Management Plugin** (optional for web management interface):
   ```sh
   sudo rabbitmq-plugins enable rabbitmq_management
   ```

4. **Access the Management Interface** (if enabled):
   - Open a browser and go to `http://<server-ip>:15672/`
   - Default username and password are both `guest`.

5. **Open Ports**:
   - Ensure that ports `5672` (AMQP) and `15672` (management) are open on your firewall.

6. **Create a New User and Set Permissions**:
   ```sh
   # Create new user
   sudo rabbitmqctl add_user myapp mypassword

   # Set user tags
   sudo rabbitmqctl set_user_tags myapp administrator

   # Set permissions (configure, write, read) on virtual host
   sudo rabbitmqctl set_permissions -p / myapp ".*" ".*" ".*"

   # Optional: Remove default guest user for security
   sudo rabbitmqctl delete_user guest
   ```

7. **Verify Setup**:
   ```sh
   # List users
   sudo rabbitmqctl list_users

   # List user permissions
   sudo rabbitmqctl list_user_permissions myapp
   ```

Your RabbitMQ server is now set up and ready to accept connections from publishers and consumers.
