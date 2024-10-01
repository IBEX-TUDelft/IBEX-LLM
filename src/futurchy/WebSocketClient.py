# WebSocketClient.py

import websocket
import threading
import json
import logging
from GameHandlerFutarchy import GameHandler

# Configure Logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

class WebSocketClient:
    def __init__(self, url, game_id, recovery=None, verbose=True):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.url = url
        self.game_id = game_id
        self.recovery = recovery
        self.verbose = verbose

        # Initialize GameHandler
        self.game_handler = GameHandler(
            game_id=game_id,
            websocket_client=self,
            verbose=verbose,
            recovery=recovery
        )

        # Initialize WebSocket App
        self.ws = websocket.WebSocketApp(
            url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.ws.on_open = self.on_open

        # Thread for WebSocket
        self.ws_thread = threading.Thread(target=self.run_forever, daemon=True)

    def on_message(self, ws, message):
        """
        Callback for when a message is received from the server.
        """
        if self.verbose:
            print("Received message:", message)
        self.logger.debug(f"Received message: {message}")
        self.game_handler.receive_message(message)

    def on_error(self, ws, error):
        """
        Callback for when an error occurs.
        """
        self.logger.error(f"WebSocket error: {error}")
        print(f"WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        """
        Callback for when the connection is closed.
        """
        self.logger.info(f"WebSocket closed with code: {close_status_code}, message: {close_msg}")
        print(f"WebSocket closed with code: {close_status_code}, message: {close_msg}")

    def on_open(self, ws):
        """
        Callback for when the connection is opened.
        """
        self.logger.info("WebSocket connection opened.")
        print("### Connection is open ###")
        initial_message = json.dumps({
            "gameId": self.game_id,
            "type": "join",
            "recovery": self.recovery
        })

        if self.verbose:
            print("Sending initial message:", initial_message)
        self.send_message(initial_message)

    def send_message(self, message):
        """
        Sends a message through the WebSocket.
        """
        try:
            if self.verbose:
                print("Sending message:", message)
            self.ws.send(message)
            self.logger.debug(f"Sent message: {message}")
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")

    def run_forever(self):
        """
        Runs the WebSocket client forever.
        """
        self.ws.run_forever(ping_interval=30, ping_timeout=10)

    def start(self):
        """
        Starts the WebSocket client in a separate thread.
        """
        self.ws_thread.start()
        self.logger.info("WebSocket client started.")
        print("WebSocket client started.")

    def stop(self):
        """
        Stops the WebSocket client.
        """
        self.ws.close()
        self.logger.info("WebSocket client stopped.")
        print("WebSocket client stopped.")

