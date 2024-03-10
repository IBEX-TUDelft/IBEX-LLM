#!/bin/bash

# Function to kill process on a given port
kill_port_process() {
    PORT=$1
    echo "Checking for processes on port $PORT..."
    PID=$(lsof -ti:$PORT)
    if [ ! -z "$PID" ]; then
        echo "Killing process on port $PORT..."
        kill -9 $PID
        wait $PID
    fi
}

# Kill processes on ports 3088 and 3080
kill_port_process 3088
kill_port_process 3080
kill_port_process 8080

# Navigate to the first directory and run the node server
echo "Starting the node server in /Users/jasperbruin/Documents/harberger-vue/api/"
cd /Users/jasperbruin/Documents/harberger-vue/api/ || exit
bash -c "node server.js" &
PID=$!
disown $PID

# Navigate to the second directory and start the Vue app
echo "Starting the Vue app in /Users/jasperbruin/Documents/harberger-vue/my-app/"
cd /Users/jasperbruin/Documents/harberger-vue/my-app/ || exit
npm run serve &
PID=$!
disown $PID

echo "Both commands are now running in the background."
