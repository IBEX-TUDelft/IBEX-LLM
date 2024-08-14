import json
import time
import random
from openai import OpenAI
import logging

class GameHandler:
    """
    Handles game logic and communication with the OpenAI API for a double auction market economic simulation.
    """

    def __init__(self, game_id, verbose=False):
        self.game_id = game_id
        self.player_wallet = None
        self.orders = {}
        self.events = []
        self.current_phase = 1
        self.current_round = 1
        self.client = OpenAI()
        self.verbose = verbose
        self.message_stack = []
        self.fixed_wait_time = 1  # fixed wait time in seconds
        self.user_number = None  # Initialize user number
        self.send_initial_message()

    def send_initial_message(self):
        initial_message = {
            "role": "system",
            "content": "You are participating in a double auction market economic simulation."
        }
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[initial_message],
            )
            if self.verbose:
                print(f"Initial LLM response: {response}")
        except Exception as e:
            logging.error(f"Error sending initial message to LLM: {e}")

    def process_message(self, message):
        logging.info(f"Received message: {message}")
        message_data = json.loads(message)

        event_type = message_data['type']
        if event_type == 'event':
            self.handle_event(message_data)

    def handle_event(self, event_data):
        event_type = event_data['eventType']
        data = event_data['data']

        if event_type == 'player-joined':
            self.update_player_wallet(data)
            self.user_number = data['number']  # Update user number

        if event_type in ['add-order', 'delete-order', 'asset-movement', 'contract-fulfilled']:
            self.query_openai(event_type, data)

    def update_player_wallet(self, data):
        self.player_wallet = data['wallet']
        if self.verbose:
            print(f"Updated player wallet: {self.player_wallet}")

    def query_openai(self, event_type, data):
        try:
            prompt = self.prepare_prompt(event_type, data)
            print(f"Querying OpenAI for event: {event_type} with prompt: {prompt}")
            message = [{"role": "user", "content": prompt}]

            start_time = time.time()
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=message,
            )
            end_time = time.time()
            reaction_time = end_time - start_time

            self.process_openai_response(response, event_type, data)
            # if self.verbose:
            #     print(f"Reaction time: {reaction_time:.2f} seconds")

            time.sleep(self.fixed_wait_time)
            self.fixed_wait_time = random.uniform(2, 5)

        except Exception as e:
            logging.error(f"Error communicating with OpenAI: {e}")

    def prepare_prompt(self, event_type, data):
        recent_context = "\n".join([f"{msg['event_type']} by user {msg['data'].get('order', {}).get('sender', 'unknown')}" if 'order' in msg['data'] else f"{msg['event_type']}" for msg in self.message_stack[-3:]])
        balance = self.player_wallet['balance']
        shares = self.player_wallet['shares']

        if event_type == 'add-order':
            sender = data['order'].get('sender', 'unknown')
            price = data['order']['price']
            quantity = data['order']['quantity']
            return (f"I currently have a wallet balance of {balance} and shares {shares}. Another user {sender} added a new order with price {price} and quantity {quantity}. "
                    f"Based on the context: {recent_context}, should I place a bid, ask, or cancel an order? Reply with 'bid X' where X is an integer less than {balance}, "
                    f"'ask Y' where Y is an integer representing the price you want to sell for, or 'cancel-order Z' where Z is the id of the order to cancel.")
        elif event_type == 'delete-order':
            return (f"An order has been deleted. Based on the context: {recent_context}, should I place a bid, ask, or cancel an order? Reply with 'bid X' where X is an integer less than {balance}, "
                    f"'ask Y' where Y is an integer representing the price you want to sell for, or 'cancel-order Z' where Z is the id of the order to cancel.")
        elif event_type == 'asset-movement':
            total_value = data['movement']['total']
            return (f"An asset movement occurred with a total value of {total_value}. Based on the context: {recent_context}, should I place a bid, ask, or cancel an order? "
                    f"Reply with 'bid X' where X is an integer less than {balance}, 'ask Y' where Y is an integer representing the price you want to sell for, or 'cancel-order Z' where Z is the id of the order to cancel.")
        return (f"Based on the context: {recent_context}, should I place a bid, ask, or cancel an order? Reply with 'bid X' where X is an integer less than {balance}, "
                f"'ask Y' where Y is an integer representing the price you want to sell for, or 'cancel-order Z' where Z is the id of the order to cancel.")

    def process_openai_response(self, response, event_type, data):
        response_text = response.choices[0].message.content
        message = None
        print(f"OpenAI Response: {response_text}")

        # Parse response and create JSON message
        response_parts = response_text.split()
        action = response_parts[0].lower()
        value = int(response_parts[1])

        if action == 'bid':
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
                "number": self.user_number,  # Use the user number here
                "phase": self.current_phase,
                "round": self.current_round,
                "type": "message"
            }
        elif action == 'ask':
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
            message = {
                "content": {
                    "order": {
                        "id": value
                    },
                    "gameId": self.game_id,
                    "type": "cancel-order"
                },
                "number": self.user_number,
                "phase": self.current_phase,
                "round": self.current_round,
                "type": "message"
            }

        # Pass the message to process_websocket_message
        self.process_websocket_message(json.dumps(message))

    def process_websocket_message(self, message):
        # This function is being called from WebSocketClient.py which is sending the message to the server.
        self.process_message(message)

        # message = [message]
        return message