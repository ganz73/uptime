#!/bin/bash

# Docker Stop Script for Uptime Monitor
echo -e "\033[33mStopping Uptime Monitor container...\033[0m"

# Stop the container
if docker stop uptime-monitor 2>/dev/null; then
    echo -e "\033[32mContainer stopped successfully.\033[0m"
else
    echo -e "\033[36mContainer was not running.\033[0m"
fi

# Remove the container
if docker rm uptime-monitor 2>/dev/null; then
    echo -e "\033[32mContainer removed successfully.\033[0m"
else
    echo -e "\033[36mNo container to remove.\033[0m"
fi

echo -e "\n\033[32mUptime Monitor has been stopped and cleaned up.\033[0m"
echo -e "\033[36mYour logs are still preserved in: $HOME/uptime_logs\033[0m"