# __init__.py

import re
import websocket
from WebSocketClient import WebSocketClient
import logging
import time


def parse_url(url):
    """
    Parse the URL to extract the hostname, endpoint, gameId, and recovery token.

    Expected URL format:
    http://<hostname>/<endpoint>/<gameId>/<recovery>

    Example:
    http://example.com/game/12345/abcde-recovery-token
    """
    # Updated regex to handle optional port and more flexible endpoint naming
    # Groups:
    # 1. Hostname (excluding port)
    # 2. Endpoint
    # 3. Game ID (digits)
    # 4. Recovery Token (alphanumerics and hyphens)
    match = re.search(r'https?://([^/:]+)(?::\d+)?/([\w-]+)/(\d+)/([\w-]+)',
                      url)
    if match:
        hostname = match.group(1)
        endpoint = match.group(2)
        game_id = int(match.group(3))
        recovery = match.group(4)
        return hostname, endpoint, game_id, recovery
    else:
        raise ValueError(
            "URL format is incorrect. Expected format: "
            "http://<hostname>/<endpoint>/<gameId>/<recovery>"
        )


if __name__ == "__main__":
    # Configure basic logging for the main script
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger("Main")

    # Disable WebSocket trace for cleaner output
    websocket.enableTrace(False)

    # Prompt user for the URL input
    url_input = input(
        "Enter the game URL (e.g., http://hostname/endpoint/gameId/recovery): ").strip()

    try:
        # Parse the input URL to extract necessary components
        hostname, endpoint, game_id, recovery = parse_url(url_input)
        logger.info(
            f"Parsed URL successfully: Hostname={hostname}, Endpoint={endpoint}, Game ID={game_id}, Recovery={recovery}")

        # Construct the WebSocket URL with the specified port (3088)
        ws_url = f"ws://{hostname}:3088/{endpoint}"
        logger.info(f"Constructed WebSocket URL: {ws_url}")
        print(f"Connecting to WebSocket URL: {ws_url}")

        # Initialize the WebSocketClient with the constructed URL and extracted parameters
        client = WebSocketClient(
            url=ws_url,
            game_id=game_id,
            recovery=recovery,
            verbose=True  # Set to True for detailed output
        )

        # Start the WebSocket client in a separate thread
        client.start()
        logger.info("WebSocket client started.")
        print("WebSocket client is running. Press Ctrl+C to exit.")

        # Keep the main thread alive to allow the WebSocket client to operate
        try:
            while True:
                time.sleep(1)  # Sleep to reduce CPU usage
        except KeyboardInterrupt:
            logger.info(
                "KeyboardInterrupt received. Stopping the WebSocket client...")
            print("\nInterrupt received, stopping the client...")
            client.stop()
            logger.info("WebSocket client stopped.")
            print("Client stopped gracefully.")

    except ValueError as ve:
        logger.error(f"ValueError: {ve}")
        print(f"Error: {ve}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        print(f"An unexpected error occurred: {e}")
