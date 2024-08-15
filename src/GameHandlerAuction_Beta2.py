import json
import time
import threading
from queue import Queue
from openai import OpenAI
import logging

# TODO: Game state met publieke informatie zoals balance en shares moeten vanuit de server geupdate worden.
# TODO: Add player id to orders
# TODO: Minimaal 1 share per persoon
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
        try:
            message_data = json.loads(message)
            event_type = message_data.get('eventType', '')

            # Parse the user number if available
            if 'number' in message_data:
                self.user_number = message_data['number']

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

        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode message JSON: {e}")
        except Exception as e:
            logging.error(f"Unexpected error in receive_message: {e}")

    def dispatch_summary(self):
        """
        Summarizes and dispatches the collected messages to the LLM agent at regular intervals.
        """
        if not self.message_queue.empty():
            # Aggregate messages
            messages_to_summarize = []
            while not self.message_queue.empty():
                messages_to_summarize.append(self.message_queue.get())

            try:
                summary = self.summarize_messages(messages_to_summarize)
                self.query_openai(summary)
            except Exception as e:
                logging.error(f"Error during dispatch_summary: {e}")
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

        # Track additional context
        total_bid_price = 0
        total_ask_price = 0
        bid_count = 0
        ask_count = 0

        for priority, message in messages:  # Unpack the tuple
            try:
                message_data = json.loads(
                    message)  # Now safely parse the JSON string
                event_type = message_data['type']

                if event_type == 'event':
                    event_name = message_data['eventType']
                    if event_name in ['add-order', 'delete-order']:
                        order_id = message_data['data']['order']['id']
                        order_data = message_data['data']['order']
                        order_price = order_data.get('price')

                        if order_price is None:
                            logging.warning(
                                f"Order {order_id} has a null price and will be skipped.")
                            continue

                        # Handle extremely high prices
                        if order_price > 1000:
                            logging.warning(
                                f"Order {order_id} has an unusually high price ({order_price}) and may skew averages.")

                        if event_name == 'add-order':
                            order_events[order_id] = order_data

                            # Track bid/ask data
                            if order_data['type'] == 'bid':
                                total_bid_price += order_price
                                bid_count += 1
                            elif order_data['type'] == 'ask':
                                total_ask_price += order_price
                                ask_count += 1

                        elif event_name == 'delete-order':
                            order_events.pop(order_id, None)

                    elif event_name == 'contract-fulfilled':
                        contract_events.append(message_data['data'])

                else:
                    logging.warning(f"Unhandled event type: {event_type}")

            except Exception as e:
                logging.error(f"Error processing message: {e}")

        # Constructing the summary
        for order_id, order_data in order_events.items():
            summary += f"Order {order_id}: {order_data['type']} at price {order_data['price']} is in the book.\n"

        for contract in contract_events:
            summary += f"Contract fulfilled from Order {contract['from']} to Order {contract['to']} at price {contract['price']}.\n"

        # Add market context
        if bid_count > 0:
            average_bid_price = total_bid_price / bid_count
            summary += f"Average Bid Price: {average_bid_price:.2f}\n"
        if ask_count > 0:
            average_ask_price = total_ask_price / ask_count
            summary += f"Average Ask Price: {average_ask_price:.2f}\n"
        summary += f"Total Bids: {bid_count}, Total Asks: {ask_count}\n"

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
                "'do nothing', 'bid X', 'ask Y', or 'cancel-order Z', where X, Y are values, and Z is an Order ID that needs to be cancelled. "
                "Also end your response with a reason with a | separator. "
                "Contract fulfilled cannot be canceled, so don't cancel-order for contract-fulfilled events. "
                "Your response should be in JSON format."
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

        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode OpenAI response JSON: {e}")
        except KeyError as e:
            logging.error(f"Key error in processing OpenAI response: {e}")
        except Exception as e:
            logging.error(f"Error communicating with OpenAI: {e}")

    def process_websocket_message(self, response_text):
        try:
            # Parse the response as JSON
            response_data = json.loads(response_text)

            # Consider both 'action' and 'response' fields
            action = response_data.get('action') or response_data.get(
                'response')

            if not action:
                logging.warning(
                    "LLM response is missing both 'action' and 'response' fields.")
                return None

            if action.lower() == 'bid':
                value = response_data.get('value')
                if value is None:
                    logging.warning("Bid value is missing in LLM response.")
                    return None
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
            elif action.lower() == 'ask':
                value = response_data.get('value')
                if value is None:
                    logging.warning("Ask value is missing in LLM response.")
                    return None
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
            elif action.lower() == 'cancel-order':
                order_id = response_data.get('order_id')
                if order_id is None:
                    logging.warning(
                        "Order ID is missing for cancel-order in LLM response.")
                    return None
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
            elif action.lower() == 'do nothing':
                if self.verbose:
                    print("LLM suggested no action.")
                return None  # Explicitly handle 'do nothing'
            else:
                logging.warning(f"Unexpected action type from LLM: {action}")
                return None

            # Convert the message to JSON and return it
            message_json = json.dumps(message)
            return message_json

        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse LLM response as JSON: {e}")
            return None
        except Exception as e:
            logging.error(
                f"Unexpected error in process_websocket_message: {e}")
            return None

    def update_player_wallet(self, data):
        """
        Updates the player's wallet information based on the incoming data.

        Args:
            data (dict): The data containing wallet information.
        """
        try:
            self.player_wallet = data['wallet']
            if self.verbose:
                print(f"Updated player wallet: {self.player_wallet}")
        except KeyError as e:
            logging.error(
                f"Missing wallet information in update_player_wallet: {e}")
        except Exception as e:
            logging.error(f"Unexpected error in update_player_wallet: {e}")

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
            try:
                self.websocket_client.ws.send(message)
            except Exception as e:
                logging.error(
                    f"Error sending message to WebSocket client: {e}")
        else:
            if self.verbose:
                print(f"Message to send: {message}")
                print("WebSocket client is not available to send the message.")
