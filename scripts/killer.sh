#!/bin/bash

# Function to kill process on a given port
kill_port_process() {
    PORT=$1
    echo "Checking for processes on port $PORT..."
    PID=$(lsof -ti:$PORT)
    if [ ! -z "$PID" ]; then
        echo "Killing process on port $PORT..."
        kill -9 $PID
        sleep 2 # Wait a bit to ensure the process has been killed
    fi
}

# Kill processes on ports 3088 and 3080
kill_port_process 3088
kill_port_process 3080
kill_port_process 8080