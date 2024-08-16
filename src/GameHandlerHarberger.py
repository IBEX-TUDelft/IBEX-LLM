import json
import time
import threading
from queue import Queue
from openai import OpenAI
import logging

class GameHandler:
    def __init__(self, game_id, websocket_client=None, verbose=False):
        # Initialize attributes
        self.game_id = game_id
        self.verbose = verbose
        self.client = OpenAI()
        self.message_queue = Queue(maxsize=20)
        self.dispatch_interval = 10
        self.player_wallet = {}
        self.user_number = None
        self.user_role = None
        self.current_phase = 1
        self.current_round = 1
        self.websocket_client = websocket_client
        self.roles = {}  # Store player roles, e.g., {'user_number': 'owner'}
        self.properties = {}  # Store property values for each user

        # Start the dispatch timer
        self.dispatch_timer = threading.Timer(self.dispatch_interval,
                                              self.dispatch_summary)
        self.dispatch_timer.start()

    def receive_message(self, message):
        try:
            message_data = json.loads(message)
            event_type = message_data.get('eventType', '')

            if event_type == 'assign-name':
                self.user_number = message_data['data']['number']
            elif event_type == 'players-known':
                self.handle_players_known(message_data['data']['players'])
            elif event_type == 'assign-role':
                self.handle_assign_role(message_data['data'])
            else:
                self.message_queue.put((2, message))  # Default priority

            if self.verbose:
                print(f"Message received: {message}")

        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode message JSON: {e}")
        except Exception as e:
            logging.error(f"Unexpected error in receive_message: {e}")

    def handle_players_known(self, players):
        for player in players:
            number = player['number']
            role = player['role']
            self.roles[number] = role
            if number == self.user_number:
                self.user_role = role
        if self.verbose:
            print(f"Player roles known: {self.roles}")

    def handle_assign_role(self, data):
        try:
            role = data['role']
            self.user_role = role
            if self.verbose:
                print(f"User assigned role: {self.user_role}")

            # Additional logic to handle wallet, property, and other data
            self.update_player_wallet(data.get('wallet'))
            self.properties[self.user_number] = data.get('property', {})

        except KeyError as e:
            logging.error(f"Missing key in handle_assign_role: {e}")

    def update_player_wallet(self, wallet_data):
        try:
            if wallet_data:
                self.player_wallet = wallet_data
                if self.verbose:
                    print(f"Updated player wallet: {self.player_wallet}")
        except Exception as e:
            logging.error(f"Unexpected error in update_player_wallet: {e}")

    def summarize_messages(self, messages):
        """
        Summarizes the collected messages into a single query.

        Args:
            messages (list): List of messages to be summarized.

        Returns:
            str: The summarized query string.
        """
        summary = "Simulation Events Summary:\n"
        role_map = {1: "Speculator", 2: "Developer", 3: "Owner"}

        for index, message in enumerate(messages):
            try:
                print(
                    f"Processing message {index + 1}/{len(messages)}: {message}")
                message_data = json.loads(message)
                event_type = message_data['eventType']
                print(f"Event type: {event_type}")

                if event_type == 'assign-role':
                    role = message_data['data']['role']
                    summary += f"Assigned role: {role_map.get(role, 'Unknown')}.\n"
                elif event_type == 'players-known':
                    summary += "Players' roles known:\n"
                    for player in message_data['data']['players']:
                        role = role_map.get(player['role'], 'Unknown')
                        summary += f" - Player {player['number']} is a {role}.\n"
                elif event_type == 'profit':
                    total = message_data['data'].get('total', 0)
                    summary += f"Profit recorded: {total} for Player {message_data['data'].get('owner')}.\n"
                elif event_type == 'declarations-published':
                    declarations = message_data['data'].get('declarations', [])
                    for declaration in declarations:
                        owner = declaration.get('owner')
                        values = declaration.get('d', [])
                        summary += f"Declaration for {owner}: {values}.\n"
                # Add other event types as needed

            except ValueError as ve:
                print(
                    f"ValueError: {ve} - Possibly an issue with JSON parsing.")
                logging.error(f"ValueError in summarize_messages: {ve}")
            except KeyError as ke:
                print(
                    f"KeyError: {ke} - Missing expected key in message data.")
                logging.error(f"KeyError in summarize_messages: {ke}")
            except Exception as e:
                print(f"General Error: {e}")
                logging.error(
                    f"Error processing message {index + 1}/{len(messages)}: {e}")

        if self.verbose:
            print(f"Message Summary: {summary}")

        return summary

    def dispatch_summary(self):
        """
        Summarizes and dispatches the collected messages to the LLM agent at regular intervals.
        """
        print("Dispatch summary started.")

        if not self.message_queue.empty():
            print(f"Queue size before dispatch: {self.message_queue.qsize()}")

            messages_to_summarize = []

            while not self.message_queue.empty():
                item = self.message_queue.get()

                # Debugging output
                print(f"Retrieved item from queue: {item}")
                print(f"Item type: {type(item)}")

                # Ensure the item is a tuple with exactly two elements
                if isinstance(item, tuple):
                    print(f"Item is a tuple of length {len(item)}")
                    if len(item) == 2:
                        priority, message = item  # Safely unpack the tuple
                        print(
                            f"Unpacked priority: {priority}, message: {message}")
                        messages_to_summarize.append(message)
                    else:
                        print(f"Unexpected tuple length: {len(item)}")
                else:
                    print(f"Unexpected item structure in queue: {item}")
                    logging.error(
                        f"Unexpected item structure in queue: {item}")
                    continue  # Skip any improperly structured items

            print(
                f"Number of valid messages to summarize: {len(messages_to_summarize)}")

            try:
                if messages_to_summarize:  # Only summarize if there are valid messages
                    summary = self.summarize_messages(messages_to_summarize)
                    print(f"Generated summary: {summary}")
                    self.query_openai(summary)
                else:
                    print("No valid messages to summarize.")
            except Exception as e:
                print(f"Error during dispatch_summary: {e}")
                logging.error(f"Error during dispatch_summary: {e}")
        else:
            print("No messages to summarize and dispatch.")
            if self.verbose:
                print("No messages to summarize and dispatch (verbose mode).")

        print("Restarting dispatch timer.")
        self.dispatch_timer = threading.Timer(self.dispatch_interval,
                                              self.dispatch_summary)
        self.dispatch_timer.start()

    def query_openai(self, summary):
        """
        Sends the summarized query to the LLM agent with instructions.

        Args:
            summary (str): The summarized query to be sent.
        """
        try:
            instructions = (
                "You are an agent in a Harberger tax simulation. "
                "Based on the following events, please respond with an appropriate action."
                "Your response should be in JSON format."
            )

            prompt = f"{instructions}\n\nEvents Summary:\n{summary}"

            message = [{"role": "user", "content": prompt}]
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=message,
            )

            response_text = response.choices[0].message.content
            ws_message = self.process_websocket_message(response_text)
            if ws_message:
                self.send_to_websocket_client(ws_message)

        except Exception as e:
            logging.error(f"Error communicating with OpenAI: {e}")

    def process_websocket_message(self, response_text):
        """
        Processes the response text from the LLM agent and generates the appropriate WebSocket message.

        Args:
            response_text (str): The response text from the LLM agent.

        Returns:
            str: The WebSocket message to be sent.
        """
        try:
            response_data = json.loads(response_text)
            if response_data.get('type') == 'message':
                message = response_data.get('content', '')
                if message:
                    return message

        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode response JSON: {e}")
        except Exception as e:
            logging.error(f"Unexpected error in process_websocket_message: {e}")

        return None

    def send_to_websocket_client(self, message):
        """
        Sends a message to the WebSocket client.

        Args:
            message (str): The message to be sent.
        """
        if self.websocket_client:
            self.websocket_client.send_message(message)
        else:
            print(f"WebSocket client not available. Message: {message}")
            logging.error("WebSocket client not available.")

    def stop_dispatcher(self):
        """
        Stops the dispatch timer gracefully.
        """
        self.dispatch_timer.cancel()
