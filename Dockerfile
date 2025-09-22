# Use official Python image
FROM python:3.11-slim

# Install ping utility and tzdata for timezone support
RUN apt-get update && apt-get install -y iputils-ping tzdata && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy all necessary files
COPY uptime.py web_server.py ./
COPY templates templates/

# Install required Python packages
RUN pip install --no-cache-dir matplotlib flask pytz

# Create log directory
RUN mkdir -p log

# Expose port for web interface
EXPOSE 8080

# Create startup script
RUN echo '#!/bin/bash\npython uptime.py & python web_server.py' > start.sh && chmod +x start.sh

# Set default command to run both scripts
CMD ["./start.sh"]
