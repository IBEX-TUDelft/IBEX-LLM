# __init__.py

import re
import argparse
import logging
import time
import os
from WebSocketClient import WebSocketClient
from concurrent.futures import ThreadPoolExecutor
import requests
import json

# Configure global logging level
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s [%(levelname)s] %(message)s')


# Function to create and start the game
def create_and_start_game(hostname, username, password, game_parameters):
    url = f'http://{hostname}/api/v1/games/create-for-llm'
    payload = {
        "username": username,
        "password": password,
        "gameParameters": game_parameters
    }
    logging.debug(f"[DEBUG] Sending game creation request to {url} with payload: {payload}")
    response = requests.post(url, json=payload)
    data = response.json()
    logging.debug(f"[DEBUG] Received response for game creation and start: {data}")

    if data.get('status') and 'data' in data and 'id' in data['data']:
        game_id = data['data']['id']
        logging.info(f"[INFO] Game created and started successfully with ID: {game_id}")
        return game_id
    else:
        error_message = data.get('message', 'No message')
        logging.error(f"[ERROR] Game creation failed: {error_message}")
        raise Exception("Game creation failed: " + error_message)


# Function to get recovery code for each player
def get_recovery_code(hostname, game_id):
    url = f'http://{hostname}/api/v1/games/get-recovery'
    params = {"game_id": game_id}
    logging.debug(f"[DEBUG] Requesting recovery code for game ID: {game_id} from {url}")
    response = requests.get(url, params=params)
    data = response.json()
    logging.debug(f"[DEBUG] Received response for recovery code request: {data}")
    if 'data' in data and 'recovery' in data['data']:
        recovery_code = data['data']['recovery']
        logging.info(f"[INFO] Recovery code obtained: {recovery_code}")
        return recovery_code
    else:
        error_message = data.get('message', 'No message')
        logging.error(f"[ERROR] Failed to get recovery code: {error_message}")
        raise Exception("Failed to get recovery code: " + error_message)


# Function to start simulation for an agent using WebSocket
def start_simulation(hostname, endpoint, game_id, recovery, agent_id):
    try:
        if not os.path.exists('output'):
            os.makedirs('output')

        logger = logging.getLogger(f"Simulation-Agent{agent_id}")
        logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(f'output/agent{agent_id}.txt')
        fh.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        logger.addHandler(fh)
        logger.addHandler(ch)

        ws_url = f"ws://{hostname}:3088/{endpoint}"
        logger.debug(f"[DEBUG] Constructed WebSocket URL: {ws_url}")
        logger.info(f"[INFO] Connecting to WebSocket URL: {ws_url}")

        client = WebSocketClient(url=ws_url, game_id=game_id,
                                 recovery=recovery, verbose=True,
                                 logger=logger)
        client.start()
        logger.info("[INFO] WebSocket client is running.")
        while True:
            time.sleep(1)

    except Exception as e:
        logger.error(f"[ERROR] Error in simulation for agent {agent_id}: {e}")


# Main function to initiate the game and run simulations
def main():
    parser = argparse.ArgumentParser(
        description="Start multiple WebSocket simulations.")
    parser.add_argument('--players', type=int, required=True,
                        help='Number of players to start')
    parser.add_argument('--hostname', type=str, default='localhost',
                        help='Server hostname')
    parser.add_argument('--endpoint', type=str, default='wss',
                        help='WebSocket endpoint')
    parser.add_argument('--username', type=str, required=True,
                        help='Admin username')
    parser.add_argument('--password', type=str, required=True,
                        help='Admin password')
    parser.add_argument('--game_params', type=str, required=True,
                        help='Path to game parameters JSON file')

    args = parser.parse_args()
    logging.debug(f"[DEBUG] Parsed arguments: {args}")

    # Load game parameters from JSON file
    logging.debug(f"[DEBUG] Loading game parameters from: {args.game_params}")
    with open(args.game_params, 'r') as f:
        game_parameters = json.load(f)
    logging.debug(f"[DEBUG] Loaded game parameters: {game_parameters}")

    # Create and start the game
    logging.debug("[DEBUG] Attempting to create and start game")
    game_id = create_and_start_game(args.hostname, args.username, args.password, game_parameters)
    logging.debug(f"[DEBUG] Game created and started with ID: {game_id}")

    # Obtain recovery codes for each player
    logging.debug(f"[DEBUG] Attempting to obtain recovery codes for {args.players} players")
    recovery_codes = [get_recovery_code(args.hostname, game_id) for _ in range(args.players)]

    # Run simulations in parallel using ThreadPoolExecutor
    logging.debug("[DEBUG] Starting simulations for all agents")
    with ThreadPoolExecutor(max_workers=args.players) as executor:
        for idx, recovery in enumerate(recovery_codes):
            executor.submit(start_simulation, args.hostname, args.endpoint,
                            game_id, recovery, idx + 1)


if __name__ == "__main__":
    main()
