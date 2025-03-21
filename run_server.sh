#!/bin/bash

# Define paths
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$APP_DIR/venv"
LOG_FILE="$APP_DIR/app.log"

# Create log file if it doesn't exist
touch "$LOG_FILE"
echo "$(date) - Starting IoT Data Server..." >> "$LOG_FILE"

# Activate virtual environment
if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
    echo "$(date) - Virtual environment activated" >> "$LOG_FILE"
else
    echo "$(date) - ERROR: Virtual environment not found at $VENV_DIR" >> "$LOG_FILE"
    exit 1
fi

# Export Flask variables
export FLASK_APP="$APP_DIR/app.py"
export FLASK_ENV=production

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "$(date) - ERROR: Python 3 not found" >> "$LOG_FILE"
    exit 1
fi

# Run the application in the background with output to log file
cd "$APP_DIR"
(python3 app.py >> "$LOG_FILE" 2>&1) &

# Store the PID
echo $! > "$APP_DIR/app.pid"
echo "$(date) - Server started with PID: $!" >> "$LOG_FILE"
echo "IoT Data Server started. Logs available at $LOG_FILE"
echo "To stop the server, run: kill \$(cat $APP_DIR/app.pid)"
