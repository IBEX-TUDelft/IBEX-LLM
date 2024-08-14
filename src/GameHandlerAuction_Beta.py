import json
import time
import threading
from queue import Queue
from openai import OpenAI
import logging


class GameHandler:
    def __init__(self, game_id, verbose=False):
        """
        Initializes the GameHandler instance.

        Args:
            game_id (str): The unique identifier for the game.
            verbose (bool): Flag to enable verbose logging. Default is False.
            dispatch_interval (int): Interval in seconds at which to dispatch summarized queries to the LLM agent.
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
        priority = 1  # Default priority
        if event_type == 'contract-fulfilled':
            priority = 3
        elif event_type in ['add-order', 'delete-order']:
            priority = 2

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
                "Based on the following market events, please respond with one of the following actions: "
                "'do nothing', 'bid X', 'ask Y', or 'cancel-order Z', where X, Y, and Z are order IDs. "
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
            print(f"Received response from OpenAI: {response_text}")
        except Exception as e:
            logging.error(f"Error communicating with OpenAI: {e}")

    def process_websocket_message(self, response):
        """
        Processes the response from the LLM agent and converts it into an action.

        Args:
            response (str): The response from the LLM agent in text format.
        """
        if self.verbose:
            print(f"Processing LLM response: {response}")

        action, value = response.split()

        if action == 'do':
            if self.verbose:
                print("No action needed.")
            return

        message = None
        if action == 'bid':
            message = {
                "type": "post-order",
                "data": {
                    "order": {
                        "type": "bid",
                        "price": int(value),
                        "quantity": 1
                    }
                },
                "gameId": self.game_id,
                "phase": self.current_phase,
                "round": self.current_round
            }
        elif action == 'ask':
            message = {
                "type": "post-order",
                "data": {
                    "order": {
                        "type": "ask",
                        "price": int(value),
                        "quantity": 1
                    }
                },
                "gameId": self.game_id,
                "phase": self.current_phase,
                "round": self.current_round
            }
        elif action == 'cancel-order':
            message = {
                "type": "cancel-order",
                "data": {
                    "order": {
                        "id": int(value)
                    }
                },
                "gameId": self.game_id,
                "phase": self.current_phase,
                "round": self.current_round
            }

        if message:
            # Convert message to JSON and return it to be sent over the WebSocket
            return json.dumps(message)


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


# # Initialize the GameHandler
# handler = GameHandler(game_id=308, verbose=True)
#
# # Define the example messages
# messages = [
#     '{"type":"event","eventType":"player-joined","data":{"authority":"admin","number":0,"shares":1,"cash":100,"wallet":{"balance":100,"shares":1},"gameId":305,"role":0}}',
#     '{"type":"event","eventType":"add-order","data":{"order":{"id":1,"sender":1,"price":5,"quantity":1,"type":"ask"}}}',
#     '{"type":"event","eventType":"add-order","data":{"order":{"id":2,"sender":1,"price":5,"quantity":1,"type":"bid"}}}',
#     '{"type":"event","eventType":"contract-fulfilled","data":{"from":2,"to":1,"price":5,"buyerFee":0,"sellerFee":0,"median":5}}',
#     '{"type":"event","eventType":"delete-order","data":{"order":{"id":2,"type":"bid"}}}',
#     '{"type":"event","eventType":"add-order","data":{"order":{"id":3,"sender":2,"price":3,"quantity":1,"type":"bid"}}}',
#     '{"type":"event","eventType":"contract-fulfilled","data":{"from":1,"to":2,"price":3,"buyerFee":0,"sellerFee":0,"median":4}}',
#     '{"type":"event","eventType":"delete-order","data":{"order":{"id":3,"type":"bid"}}}',
#     '{"type":"event","eventType":"add-order","data":{"order":{"id":4,"sender":1,"price":4,"quantity":1,"type":"bid"}}}',
#     '{"type":"event","eventType":"contract-fulfilled","data":{"from":1,"to":2,"price":5,"buyerFee":0,"sellerFee":0,"median":5}}',
#     '{"type":"event","eventType":"delete-order","data":{"order":{"id":1,"type":"ask"}}}',
#     '{"type":"event","eventType":"contract-fulfilled","data":{"from":2,"to":1,"price":4,"buyerFee":0,"sellerFee":0,"median":4.5}}',
#     '{"type":"event","eventType":"delete-order","data":{"order":{"id":4,"type":"bid"}}}'
# ]
#
# # Feed the messages to the GameHandler
# for message in messages:
#     handler.receive_message(message)
#     time.sleep(1)  # Simulate some delay between receiving messages
#
# # Allow enough time for the dispatch to occur
# time.sleep(10)
#
# # Stop the dispatcher after testing
# handler.stop_dispatcher()

