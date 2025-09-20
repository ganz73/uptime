# Use official Python image
FROM python:3.11-slim

# Install ping utility
RUN apt-get update && apt-get install -y iputils-ping && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python script into container
COPY uptime.py ./

# Install required Python packages
RUN pip install --no-cache-dir matplotlib

# Set default command to run the script
CMD ["python", "uptime.py"]
