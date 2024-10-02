# __init__.py

import re
import argparse
import logging
import time
import os
from WebSocketClient import WebSocketClient
from concurrent.futures import ThreadPoolExecutor

def parse_url(url):
    match = re.search(r'https?://([^/:]+)(?::\d+)?/([\w-]+)/(\d+)/([\w-]+)', url)
    if match:
        hostname = match.group(1)
        endpoint = match.group(2)
        game_id = int(match.group(3))
        recovery = match.group(4)
        return hostname, endpoint, game_id, recovery
    else:
        raise ValueError("Invalid URL format. Expected format: http://<hostname>/<endpoint>/<gameId>/<recovery>")


def start_simulation(url, agent_id):
    # Ensure output directory exists
    if not os.path.exists('output'):
        os.makedirs('output')

    logger = logging.getLogger(f"Simulation-Agent{agent_id}")
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(f'output/agent{agent_id}.txt')
    fh.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    try:
        hostname, endpoint, game_id, recovery = parse_url(url)
        logger.info(f"Parsed URL successfully: Hostname={hostname}, Endpoint={endpoint}, Game ID={game_id}, Recovery={recovery}")

        ws_url = f"ws://{hostname}:3088/{endpoint}"
        logger.info(f"Constructed WebSocket URL: {ws_url}")
        logger.info(f"Connecting to WebSocket URL: {ws_url}")

        client = WebSocketClient(url=ws_url, game_id=game_id, recovery=recovery, verbose=True, logger=logger)
        client.start()
        logger.info("WebSocket client is running.")

        while True:
            time.sleep(1)

    except Exception as e:
        logger.error(f"Error in simulation: {e}")


def main():
    parser = argparse.ArgumentParser(description="Start multiple WebSocket simulations.")
    parser.add_argument('urls', nargs='+', help='List of URLs for each agent')

    args = parser.parse_args()

    N = len(args.urls)

    with ThreadPoolExecutor(max_workers=N) as executor:
        for idx, url in enumerate(args.urls):
            agent_id = idx + 1
            executor.submit(start_simulation, url, agent_id)


if __name__ == "__main__":
    main()
