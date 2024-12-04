"""
To spawn agents we need to:

curl -X POST "http://localhost:10341/spawn-agents" \
     -H "Content-Type: application/json" \
     -d '{
        "game_id": 141,
        "agents": 12,
        "game_type": "harberger"
     }'


"""

import os
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
import requests
from WebSocketClient import WebSocketClient

# Load environment variables
load_dotenv()
PORT = int(os.getenv("PORT", 10341))
HOSTNAME = os.getenv("HOSTNAME", "localhost")

# Configure global logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s [%(levelname)s] %(message)s')

# Initialize Flask app
app = Flask(__name__)


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


# Spawn agents with dynamic parameters
@app.route('/spawn-agents', methods=['POST'])
def spawn_agents():
    try:
        # Parse and validate input data
        data = request.json
        if not data:
            raise ValueError("Request payload must be JSON.")

        game_id = data.get('game_id')
        agents = data.get('agents')
        game_type = data.get('game_type')

        if not game_id:
            raise ValueError("Missing required parameter: 'game_id'")
        if not agents:
            raise ValueError("Missing required parameter: 'agents'")
        if not game_type:
            raise ValueError("Missing required parameter: 'game_type'")

        logging.info(
            f"Starting game with ID: {game_id}, Agents: {agents}, Game Type: {game_type}")

        # Obtain recovery codes for each agent
        recovery_codes = [get_recovery_code(HOSTNAME, game_id) for _ in
                          range(agents)]

        # Start simulations in parallel, logging to separate files for each agent
        with ThreadPoolExecutor(max_workers=agents) as executor:
            for idx, recovery_code in enumerate(recovery_codes):
                executor.submit(start_simulation, HOSTNAME, 'wss', game_id,
                                recovery_code, idx + 1)

        return jsonify({
            "message": "Agents spawned successfully",
            "game_id": game_id,
            "agents": agents,
            "game_type": game_type,
            "recovery_codes": recovery_codes
        })

    except ValueError as ve:
        logging.error(f"Validation Error: {ve}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


# Start WebSocket simulation
def start_simulation(hostname, endpoint, game_id, recovery, agent_id):
    # Configure agent-specific logging
    agent_log_file = f"./output/agent{agent_id}.txt"
    os.makedirs(os.path.dirname(agent_log_file), exist_ok=True)

    agent_logger = logging.getLogger(f"Agent{agent_id}")
    agent_logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler(agent_log_file)
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    agent_logger.addHandler(file_handler)

    try:
        ws_url = f"ws://{hostname}:3088/{endpoint}"
        agent_logger.info(f"Constructed WebSocket URL: {ws_url}")
        agent_logger.info(f"Connecting to WebSocket URL: {ws_url}")

        client = WebSocketClient(url=ws_url, game_id=game_id,
                                 recovery=recovery, verbose=True,
                                 logger=agent_logger)
        client.start()

    except Exception as e:
        agent_logger.error(f"Error in simulation for Agent {agent_id}: {e}")
        raise


# Main entry point to run the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
