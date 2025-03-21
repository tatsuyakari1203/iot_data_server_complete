#!/bin/bash

# Define paths
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$APP_DIR/app.pid"
LOG_FILE="$APP_DIR/app.log"

# Check if PID file exists
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo "Stopping IoT Data Server with PID: $PID"
    
    # Try to kill the process
    if kill $PID 2>/dev/null; then
        echo "$(date) - Server with PID $PID stopped successfully" >> "$LOG_FILE"
        echo "Server stopped successfully"
        rm "$PID_FILE"
    else
        echo "$(date) - Failed to stop server with PID $PID" >> "$LOG_FILE"
        echo "Failed to stop server. Process may no longer exist."
        rm "$PID_FILE"
    fi
else
    echo "No PID file found. Server may not be running."
fi
