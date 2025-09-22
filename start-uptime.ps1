# Docker Start Script for Uptime Monitor
Write-Host "Starting Uptime Monitor container..." -ForegroundColor Green

# Stop and remove if already exists
docker stop uptime-monitor 2>$null
docker rm uptime-monitor 2>$null

# Build the latest image
Write-Host "Building Docker image..." -ForegroundColor Yellow
docker build -t uptime-monitor .

# Run the container
Write-Host "Starting container..." -ForegroundColor Yellow
docker run -d `
    -v "$HOME\uptime_logs:/app/log" `
    -v "/etc/localtime:/etc/localtime:ro" `
    -e "TZ=America/New_York" `
    -p 8080:8080 `
    --name uptime-monitor `
    uptime-monitor

# Check if container started successfully
$containerId = docker ps -q -f name=uptime-monitor
if ($containerId) {
    Write-Host "`nUptime Monitor started successfully!" -ForegroundColor Green
    Write-Host "You can access the web interface at: http://localhost:8080" -ForegroundColor Cyan
    Write-Host "Logs are being saved to: $HOME\uptime_logs" -ForegroundColor Cyan
} else {
    Write-Host "`nError: Container failed to start. Please check Docker logs." -ForegroundColor Red
}