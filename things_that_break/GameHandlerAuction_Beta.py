import json
import time
import threading
from queue import Queue
from openai import OpenAI
import logging

# TODO: User number is not being parsed correctly from the message data
# TODO: let llm to use JSON so that its easier to parse
# TODO: Give more context to the LLM for better decision making

class GameHandler:
    def __init__(self, game_id, websocket_client=None, verbose=False):
        """
        Initializes the GameHandler instance.

        Args:
            game_id (str): The unique identifier for the game.
            websocket_client (WebSocketClient): The WebSocket client instance to use for sending messages.
            verbose (bool): Flag to enable verbose logging. Default is False.
        """
        self.game_id = game_id
        self.verbose = verbose
        self.client = OpenAI()
        self.message_queue = Queue(maxsize=20)
        self.dispatch_interval = 10
        self.player_wallet = None
        self.user_number = None
        self.current_phase = 1
        self.current_round = 1
        self.websocket_client = websocket_client  # Store the WebSocket client instance

        # Start the dispatch timer
        self.dispatch_timer = threading.Timer(self.dispatch_interval,
                                              self.dispatch_summary)
        self.dispatch_timer.start()

    def receive_message(self, message):
        """
        Receives and stores incoming messages in the queue.

        Args:
            message (str): The incoming message in JSON format.
        """
        message_data = json.loads(message)
        event_type = message_data.get('eventType', '')

        # Assign priority: Higher for contract-fulfilled, lower for add-order and delete-order
        priority = 2  # Default priority
        if event_type == 'contract-fulfilled':
            priority = 3
        elif event_type in ['add-order', 'delete-order']:
            priority = 1

        if self.message_queue.full():
            # Optionally discard or prioritize based on importance
            self.message_queue.get()

        # Optionally wrap the message with priority information
        self.message_queue.put((priority, message))
        if self.verbose:
            print(f"Message received with priority {priority}: {message}")


    def dispatch_summary(self):
        """
        Summarizes and dispatches the collected messages to the LLM agent at regular intervals.
        """
        if not self.message_queue.empty():
            # Aggregate messages
            messages_to_summarize = []
            while not self.message_queue.empty():
                messages_to_summarize.append(self.message_queue.get())

            summary = self.summarize_messages(messages_to_summarize)
            self.query_openai(summary)
        else:
            if self.verbose:
                print("No messages to summarize and dispatch.")

        # Reset the timer for the next interval
        self.dispatch_timer = threading.Timer(self.dispatch_interval,
                                              self.dispatch_summary)
        self.dispatch_timer.start()

    def summarize_messages(self, messages):
        """
        Summarizes the collected messages into a single query.

        Args:
            messages (list): List of tuples containing priority and message to be summarized.

        Returns:
            str: The summarized query string.
        """
        summary = "Market Events Summary:\n"
        order_events = {}
        contract_events = []

        for priority, message in messages:  # Unpack the tuple
            message_data = json.loads(
                message)  # Now safely parse the JSON string
            event_type = message_data['type']

            if event_type == 'event':
                event_name = message_data['eventType']
                if event_name in ['add-order', 'delete-order']:
                    order_id = message_data['data']['order']['id']
                    if event_name == 'add-order':
                        order_events[order_id] = message_data['data']['order']
                    elif event_name == 'delete-order':
                        order_events.pop(order_id, None)
                elif event_name == 'contract-fulfilled':
                    contract_events.append(message_data['data'])

        # Constructing the summary
        for order_id, order_data in order_events.items():
            summary += f"Order {order_id}: {order_data['type']} at price {order_data['price']} is in the book.\n"

        for contract in contract_events:
            summary += f"Contract fulfilled from Order {contract['from']} to Order {contract['to']} at price {contract['price']}.\n"

        if self.verbose:
            print(f"Message Summary: {summary}")

        return summary

    def query_openai(self, summary):
        """
        Sends the summarized query to the LLM agent with clear instructions on the required response format.

        Args:
            summary (str): The summarized query to be sent.
        """
        try:
            # Define the instructions to guide the LLM's response format
            instructions = (
                "You are a trader in a double auction market. "
                "Based on the following market events, please respond with one of the following actions: "
                "'do nothing', 'bid X', 'ask Y', or 'cancel-order Z', where X, Y are values, and is Z a Order ID that needs to be cancelled. Also end your response with a reason with a | separator. "
                "Contract fulfilled cannot be canceled, so don't cancel-order for contract-fulfilled events."
                "Your response should strictly adhere to this format and only include one action."
            )

            # Combine the instructions with the market summary
            prompt = f"{instructions}\n\nMarket Events Summary:\n{summary}"

            # Create the message to be sent to the LLM
            message = [{"role": "user", "content": prompt}]
            print(f"Querying OpenAI with the following prompt:\n{prompt}")

            # Send the message to the LLM and process the response
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=message,
            )

            response_text = response.choices[0].message.content
            print(f"LLM Response: {response_text}")

            # Process the response and get the message to be sent back
            ws_message = self.process_websocket_message(response_text)
            if ws_message:
                # This is where you would pass the message back to WebSocketClient
                self.send_to_websocket_client(ws_message)

        except Exception as e:
            logging.error(f"Error communicating with OpenAI: {e}")

    def process_websocket_message(self, response_text):
        action = response_text.split()[0].lower()

        if action == 'bid':
            value = int(response_text.split()[1])
            message = {
                "content": {
                    "order": {
                        "price": value,
                        "quantity": 1,
                        "type": "bid",
                        "now": True
                    },
                    "gameId": self.game_id,
                    "type": "post-order"
                },
                "number": self.user_number,
                "phase": self.current_phase,
                "round": self.current_round,
                "type": "message"
            }
        elif action == 'ask':
            value = int(response_text.split()[1])
            message = {
                "content": {
                    "order": {
                        "price": value,
                        "quantity": 1,
                        "type": "ask",
                        "now": False
                    },
                    "gameId": self.game_id,
                    "type": "post-order"
                },
                "number": self.user_number,
                "phase": self.current_phase,
                "round": self.current_round,
                "type": "message"
            }
        elif action == 'cancel-order':
            order_id = int(response_text.split()[1])
            message = {
                "content": {
                    "order": {
                        "id": order_id
                    },
                    "gameId": self.game_id,
                    "type": "cancel-order"
                },
                "number": self.user_number,
                "phase": self.current_phase,
                "round": self.current_round,
                "type": "message"
            }
        else:
            if self.verbose:
                print(
                    "LLM suggested no action or gave an unexpected response.")
            return None  # No action needed

        # Convert the message to JSON and return it
        message_json = json.dumps(message)
        return message_json

    def update_player_wallet(self, data):
        """
        Updates the player's wallet information based on the incoming data.

        Args:
            data (dict): The data containing wallet information.
        """
        self.player_wallet = data['wallet']
        if self.verbose:
            print(f"Updated player wallet: {self.player_wallet}")

    def stop_dispatcher(self):
        """
        Stops the dispatch timer gracefully.
        """
        self.dispatch_timer.cancel()

    def send_to_websocket_client(self, message):
        """
        Sends the message to the WebSocket client.

        Args:
            message (str): The message in JSON format to be sent back to the WebSocket server.
        """
        if self.websocket_client and hasattr(self.websocket_client.ws, 'send'):
            print(f"Message to send: {message}")
            self.websocket_client.ws.send(message)
        else:
            if self.verbose:
                print(f"Message to send: {message}")
                print("WebSocket client is not available to send the message.")
