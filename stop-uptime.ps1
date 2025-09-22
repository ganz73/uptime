# Docker Stop Script for Uptime Monitor
Write-Host "Stopping Uptime Monitor container..." -ForegroundColor Yellow

# Stop the container
docker stop uptime-monitor
if ($?) {
    Write-Host "Container stopped successfully." -ForegroundColor Green
} else {
    Write-Host "Container was not running." -ForegroundColor Cyan
}

# Remove the container
docker rm uptime-monitor 2>$null
if ($?) {
    Write-Host "Container removed successfully." -ForegroundColor Green
} else {
    Write-Host "No container to remove." -ForegroundColor Cyan
}

Write-Host "`nUptime Monitor has been stopped and cleaned up." -ForegroundColor Green
Write-Host "Your logs are still preserved in: $HOME\uptime_logs" -ForegroundColor Cyan