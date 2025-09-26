from flask import Flask, render_template
import os
from datetime import datetime
import json

app = Flask(__name__)

LOG_DIR = "log"

def get_log_files():
    """Get a list of all log files sorted by date."""
    if not os.path.exists(LOG_DIR):
        return []
    files = [f for f in os.listdir(LOG_DIR) if f.startswith("uptime_log_") and f.endswith(".log")]
    return sorted(files, reverse=True)

def read_master_summary():
    """Read the master summary file."""
    summary_file = os.path.join(LOG_DIR, "uptime_master_summary.log")
    if not os.path.exists(summary_file):
        return "No summary data available"
    with open(summary_file, 'r') as f:
        return f.read()

def read_log_file(filename):
    """Read a specific log file."""
    file_path = os.path.join(LOG_DIR, filename)
    if not os.path.exists(file_path):
        return "Log file not found"
    with open(file_path, 'r') as f:
        return f.read()

@app.route('/')
def home():
    """Display the home page with summary and log file links."""
    log_files = get_log_files()
    summary = read_master_summary()
    return render_template('index.html', 
                         summary=summary,
                         log_files=log_files)

@app.route('/logs/<date>')
def view_log(date):
    """Display a specific log file."""
    log_content = read_log_file(f"uptime_log_{date}.log")
    return render_template('log.html', 
                         date=date,
                         log_content=log_content)

def start_server():
    """Start the Flask server."""
    app.run(host='0.0.0.0', port=8080)

if __name__ == '__main__':
    start_server()