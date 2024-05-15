#!/bin/bash

# Function to kill process on a given port
kill_port_process() {
    PORT=$1
    echo "Checking for processes on port $PORT..."
    PID=$(lsof -ti:$PORT)
    if [ ! -z "$PID" ]; then
        echo "Killing process on port $PORT..."
        kill -9 $PID
        wait $PID 2>/dev/null
    fi
}

# Kill processes on ports 3088, 3080, and 8080
kill_port_process 3088
kill_port_process 3080
kill_port_process 8080

# Navigate to the first directory and run the node server
echo "Starting the node server in /Users/jasperbruin/Documents/harberger-vue/api/"
cd /Users/jasperbruin/Documents/harberger-vue/api/ || exit
node server.js &
PID=$!
disown $PID

# Navigate to the second directory and start the Vue app
echo "Starting the Vue app in /Users/jasperbruin/Documents/harberger-vue/my-app/"
cd /Users/jasperbruin/Documents/harberger-vue/my-app/ || exit
npm run serve &
PID=$!
disown $PID

# Wait for servers to start up (adjust sleep time as necessary)
sleep 5

# Send a request to start a game and capture the raw response
echo "Starting game..."
RAW_RESPONSE=$(curl -s -X POST "http://localhost:3080/start-game" -H "Content-Type: application/json")
echo "Raw response from start-game endpoint: $RAW_RESPONSE"

# Parse GAME_ID from the raw response
GAME_ID=$(echo $RAW_RESPONSE | jq -r '.gameId')

# Check if GAME_ID was received
if [ -z "$GAME_ID" ] || [ "$GAME_ID" == "null" ]; then
  echo "Failed to start game"
  exit 1
fi

echo "Game ID: $GAME_ID"

# Send requests to add two players
echo "Adding Player 1 to game $GAME_ID..."
PLAYER1_ID=$(curl -s -X POST "http://localhost:3080/add-player" -H "Content-Type: application/json" -d '{"gameId": "'$GAME_ID'", "playerId": "1"}' | jq -r '.playerId')
echo "Adding Player 2 to game $GAME_ID..."
PLAYER2_ID=$(curl -s -X POST "http://localhost:3080/add-player" -H "Content-Type: application/json" -d '{"gameId": "'$GAME_ID'", "playerId": "2"}' | jq -r '.playerId')

echo "Both commands are now running in the background. Game $GAME_ID started with two players."

# Run Python script with Game ID and Player ID
python3 /path/to/Problem.py $GAME_ID $PLAYER1_ID
