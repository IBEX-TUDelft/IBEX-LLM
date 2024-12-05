# WebSocketClient.py

import websocket
import threading
import json
import logging
from GameHandlerFuturchy import GameHandler

class WebSocketClient:
    def __init__(self, url, game_id, recovery=None, verbose=True, logger=None):
        self.logger = logger or logging.getLogger(f"WebSocketClient-{game_id}")
        self.url = url
        self.game_id = game_id
        self.recovery = recovery
        self.verbose = verbose

        self.game_handler = GameHandler(
            game_id=game_id,
            websocket_client=self,
            verbose=verbose,
            recovery=recovery,
            logger=self.logger
        )

        self.ws = websocket.WebSocketApp(
            url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.ws.on_open = self.on_open

        self.ws_thread = threading.Thread(target=self.run_forever, daemon=True)

    def on_message(self, ws, message):
        if self.verbose:
            self.logger.info(f"Received message: {message}")
        else:
            self.logger.debug(f"Received message: {message}")
        self.game_handler.receive_message(message)

    def on_error(self, ws, error):
        self.logger.error(f"WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        self.logger.info(f"WebSocket closed with code: {close_status_code}, message: {close_msg}")

    def on_open(self, ws):
        self.logger.info("WebSocket connection opened.")
        initial_message = json.dumps({
            "gameId": self.game_id,
            "type": "join",
            "recovery": self.recovery
        })

        if self.verbose:
            self.logger.debug(f"Sending initial message: {initial_message}")
        self.send_message(initial_message)

    def send_message(self, message):
        try:
            if self.verbose:
                self.logger.info(f"Sending message: {message}")
            else:
                self.logger.debug(f"Sending message: {message}")
            self.ws.send(message)
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")

    def run_forever(self):
        self.ws.run_forever(ping_interval=30, ping_timeout=10)

    def start(self):
        self.ws_thread.start()
        self.logger.info("WebSocket client started.")

    def stop(self):
        self.ws.close()
        self.logger.info("WebSocket client stopped.")
