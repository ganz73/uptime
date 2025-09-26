#!/bin/bash

# Docker Start Script for Uptime Monitor
echo -e "\033[32mStarting Uptime Monitor container...\033[0m"

# Stop and remove if already exists
docker stop uptime-monitor 2>/dev/null
docker rm uptime-monitor 2>/dev/null

# Build the latest image
echo -e "\033[33mBuilding Docker image...\033[0m"
docker build -t uptime-monitor .

# Run the container
echo -e "\033[33mStarting container...\033[0m"
docker run -d \
    -v "$HOME/uptime_logs:/app/log" \
    -e "TZ=America/New_York" \
    -p 8080:8080 \
    --name uptime-monitor \
    uptime-monitor

# Check if container started successfully
containerId=$(docker ps -q -f name=uptime-monitor)
if [ -n "$containerId" ]; then
    echo -e "\n\033[32mUptime Monitor started successfully!\033[0m"
    echo -e "\033[36mYou can access the web interface at: http://localhost:8080\033[0m"
    echo -e "\033[36mLogs are being saved to: $HOME/uptime_logs\033[0m"
else
    echo -e "\n\033[31mError: Container failed to start. Please check Docker logs.\033[0m"
fi