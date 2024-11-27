"""
To spawn agents we need to:

curl -X POST "http://localhost:10341/spawn-agents" \
     -H "Content-Type: application/json" \
     -d '{
         "game_id": 139,
         "game_type": "harberger",
         "hostname": "188.166.34.67"
     }'
"""


import os
import json
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
import requests
from WebSocketClient import WebSocketClient

# Load environment variables
load_dotenv()
PORT = int(os.getenv("PORT", 10341))

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

# Initialize Flask app
app = Flask(__name__)

# Function to get recovery code for a game
def get_recovery_code(hostname, game_id):
    url = f'http://{hostname}/api/v1/games/get-recovery'
    params = {"game_id": game_id}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        print(f"Recovery code: {data['data']['recovery']}")
        return data['data']['recovery']
    else:
        raise Exception(f"Failed to get recovery code: {response.text}")

# Spawn agents
@app.route('/spawn-agents', methods=['POST'])
def spawn_agents():
    try:
        data = request.json
        hostname = data['hostname']
        game_id = data['game_id']
        players = data.get('players', 1)  # Default to 1 player if not specified

        # Obtain recovery codes
        recovery_codes = [get_recovery_code(hostname, game_id) for _ in range(players)]

        # Start simulations in parallel
        with ThreadPoolExecutor(max_workers=players) as executor:
            for idx, recovery_code in enumerate(recovery_codes):
                executor.submit(start_simulation, hostname, 'wss', game_id, recovery_code, idx + 1)

        return jsonify({
            "message": "Agents spawned successfully",
            "game_id": game_id,
            "recovery_codes": recovery_codes
        })

    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

# Start WebSocket simulation
def start_simulation(hostname, endpoint, game_id, recovery, agent_id):
    ws_url = f"ws://{hostname}:3088/{endpoint}"
    client = WebSocketClient(
        url=ws_url,
        game_id=game_id,
        recovery=recovery,
        verbose=True,
        logger=logging.getLogger(f"Agent{agent_id}")
    )
    client.start()

# Main entry point to run the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)

