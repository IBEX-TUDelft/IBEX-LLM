import os
import json
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
import requests
from WebSocketClient import WebSocketClient
import argparse

# Load environment variables
load_dotenv()
PORT = int(os.getenv("PORT", 10341))

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

# Initialize Flask app
app = Flask(__name__)

# Function to create and start the game
def create_and_start_game(hostname, username, password, game_parameters):
    url = f'http://{hostname}/api/v1/games/create-for-llm'
    payload = {
        "username": username,
        "password": password,
        "gameParameters": game_parameters
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        data = response.json()
        if data.get('status') and 'data' in data and 'id' in data['data']:
            return data['data']['id']
        else:
            raise Exception(data.get('message', 'Game creation failed'))
    else:
        raise Exception(f"Failed to create game: {response.text}")

# Function to get recovery code for a game
def get_recovery_code(hostname, game_id):
    url = f'http://{hostname}/api/v1/games/get-recovery'
    params = {"game_id": game_id}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data['data']['recovery']
    else:
        raise Exception(f"Failed to get recovery code: {response.text}")

# Validate game parameters against a schema
def validate_game_params(game_params):
    # Add schema validation logic here if needed (using jsonschema or custom checks)
    required_keys = ["title", "tax_rate", "signal", "speculators", "developers", "owners", "timers", "round_count"]
    for key in required_keys:
        if key not in game_params:
            raise ValueError(f"Missing required key in game parameters: {key}")

# Spawn agents
@app.route('/spawn-agents', methods=['POST'])
def spawn_agents():
    try:
        data = request.json
        players = data['players']
        hostname = data['hostname']
        username = data['username']
        password = data['password']
        game_params_path = data['game_params']

        # Load and validate game parameters
        with open(game_params_path, 'r') as f:
            game_params = json.load(f)
        validate_game_params(game_params)

        # Create and start game
        game_id = create_and_start_game(hostname, username, password, game_params)

        # Obtain recovery codes
        recovery_codes = [get_recovery_code(hostname, game_id) for _ in range(players)]

        # Start simulations in parallel
        with ThreadPoolExecutor(max_workers=players) as executor:
            for idx, recovery_code in enumerate(recovery_codes):
                executor.submit(start_simulation, hostname, 'wss', game_id, recovery_code, idx + 1)

        return jsonify({"message": "Agents spawned successfully", "game_id": game_id, "recovery_codes": recovery_codes})

    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

# Start WebSocket simulation
def start_simulation(hostname, endpoint, game_id, recovery, agent_id):
    ws_url = f"ws://{hostname}:3088/{endpoint}"
    client = WebSocketClient(url=ws_url, game_id=game_id, recovery=recovery, verbose=True, logger=logging.getLogger(f"Agent{agent_id}"))
    client.start()

# Main entry point to run the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
