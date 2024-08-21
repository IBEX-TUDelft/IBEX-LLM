import json
import threading
from queue import Queue
from openai import OpenAI
import logging

class GameHandler:
    def __init__(self, game_id, websocket_client=None, verbose=False):
        self.game_id = game_id
        self.verbose = verbose
        self.client = OpenAI()
        self.message_queue = Queue(maxsize=20)
        self.dispatch_interval = 10
        self.user_number = None  # Initialize the user number to None
        self.current_phase = 1
        self.current_round = 1
        self.websocket_client = websocket_client
        self.private_game_state = {}

        self.public_game_state = {}


        # Start the dispatch timer
        self.dispatch_timer = threading.Timer(self.dispatch_interval, self.dispatch_summary)
        self.dispatch_timer.start()

    def init_player_state(self, player_id, cash, shares):
        self.private_game_state[player_id] = {
            "shares_available": shares,
            "shares_offered_for_sale": 0,
            "cash_available": cash,
            "cash_locked_in_bids": 0
        }
        if self.verbose:
            print(f"Initialized player {player_id} with {cash} cash and {shares} shares.")

    def get_player_state(self, player_id):
        if player_id not in self.private_game_state:
            self.private_game_state[player_id] = {
                "shares_available": 0,
                "shares_offered_for_sale": 0,
                "cash_available": 0,
                "cash_locked_in_bids": 0
            }
        return self.private_game_state[player_id]

    def handle_player_joined(self, event):
        player_data = event['data']
        player_id = player_data['number']
        cash = player_data['cash']
        shares = player_data['shares']

        # Set the user number when the player joins
        self.user_number = player_id
        self.init_player_state(player_id, cash, shares)

    def handle_add_order(self, event):
        order = event['data']['order']
        player_id = order['sender']
        price = order['price']
        quantity = order['quantity']
        order_type = order['type']

        player_state = self.get_player_state(player_id)

        if order_type == 'bid':
            # Lock cash in bids, but do not deduct from cash_available yet
            player_state['cash_locked_in_bids'] += price * quantity
        elif order_type == 'ask':
            player_state['shares_offered_for_sale'] += quantity
            player_state['shares_available'] -= quantity

    def handle_contract_fulfilled(self, event):
        # Extract the necessary details from the event
        contract_data = event['data']
        seller_id = contract_data['from']
        buyer_id = contract_data['to']

        # Ensure the game state is initialized
        if seller_id not in self.public_game_state:
            self.public_game_state[seller_id] = 1  # Initialize seller's shares
        if buyer_id not in self.public_game_state:
            self.public_game_state[buyer_id] = 1  # Initialize buyer's shares

        # Handle the logic of shares after a contract is fulfilled
        # The buyer gets the quantity of shares from the seller
        # Assuming each contract fulfillment is for 1 share unless specified otherwise
        self.public_game_state[buyer_id] += 1
        self.public_game_state[seller_id] -= 1

        # Ensure that shares do not fall below 1
        if self.public_game_state[seller_id] < 1:
            self.public_game_state[seller_id] = 1

        # Print the updated game state
        print(f"Updated Public Game State: {self.public_game_state}")

    def handle_delete_order(self, event):
        order = event['data']['order']
        player_id = order['sender']
        order_type = order['type']
        price = order.get('price', 0)
        quantity = order.get('quantity', 1)

        player_state = self.get_player_state(player_id)

        if order_type == 'bid':
            player_state['cash_locked_in_bids'] = max(0, player_state[
                'cash_locked_in_bids'] - price * quantity)
            player_state['cash_available'] += price * quantity
        elif order_type == 'ask':
            player_state['shares_offered_for_sale'] = max(0, player_state[
                'shares_offered_for_sale'] - quantity)
            player_state['shares_available'] += quantity

    def update_private_game_state(self, events):
        for event_json in events:
            event = json.loads(event_json)

            if event['eventType'] == 'player-joined':
                self.handle_player_joined(event)
            elif event['eventType'] == 'add-order':
                self.handle_add_order(event)
            elif event['eventType'] == 'contract-fulfilled':
                self.handle_contract_fulfilled(event)
            elif event['eventType'] == 'delete-order':
                self.handle_delete_order(event)

        return self.private_game_state

    def receive_message(self, message):
        try:
            message_data = json.loads(message)
            event_type = message_data.get('eventType', '')

            if event_type == 'player-joined':
                # Process player-joined event immediately to set the user number
                self.handle_player_joined(message_data)

            priority = 2  # Default priority
            if event_type == 'contract-fulfilled':
                priority = 3
            elif event_type in ['add-order', 'delete-order']:
                priority = 1
            elif event_type == 'player-joined':
                priority = 4  # Ensure player-joined is processed first

            if self.message_queue.full():
                self.message_queue.get()

            self.message_queue.put((priority, message))
            if self.verbose:
                print(f"Message received with priority {priority}: {message}")

            self.update_private_game_state([message])

        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode message JSON: {e}")
        except Exception as e:
            logging.error(f"Unexpected error in receive_message: {e}")

    def dispatch_summary(self):
        if not self.message_queue.empty():
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

        self.dispatch_timer = threading.Timer(self.dispatch_interval, self.dispatch_summary)
        self.dispatch_timer.start()

    def summarize_messages(self, messages):
        summary = "Market Events Summary:\n"
        order_events = {}
        contract_events = []

        total_bid_price = 0
        total_ask_price = 0
        bid_count = 0
        ask_count = 0

        for priority, message in messages:
            try:
                message_data = json.loads(message)
                event_type = message_data['type']

                if event_type == 'event':
                    event_name = message_data['eventType']

                    if event_name == 'add-order':
                        order_id = message_data['data']['order']['id']
                        order_data = message_data['data']['order']
                        order_price = order_data.get('price')

                        if order_price is None:
                            logging.warning(
                                f"Order {order_id} has a null price and will be skipped.")
                            continue

                        if order_price > 1000:
                            logging.warning(
                                f"Order {order_id} has an unusually high price ({order_price}) and may skew averages.")

                        order_events[order_id] = order_data

                        if order_data['type'] == 'bid':
                            total_bid_price += order_price
                            bid_count += 1
                        elif order_data['type'] == 'ask':
                            total_ask_price += order_price
                            ask_count += 1

                    elif event_name == 'delete-order':
                        order_id = message_data['data']['order']['id']
                        order_events.pop(order_id, None)

                    elif event_name == 'contract-fulfilled':
                        contract_events.append(message_data['data'])

                    # Ensure to update the public game state
                    for player_id, shares in self.public_game_state.items():
                        if player_id in self.public_game_state:
                            # Make sure we aren't setting any negative values
                            if self.public_game_state[player_id] < 0:
                                self.public_game_state[player_id] = 0

                else:
                    logging.warning(f"Unhandled event type: {event_type}")

            except Exception as e:
                logging.error(f"Error processing message: {e}")

        for order_id, order_data in order_events.items():
            summary += f"Order {order_id}: {order_data['type']} at price {order_data['price']} is in the book.\n"

        for contract in contract_events:
            summary += f"Contract fulfilled from Player {contract['from']} to Player {contract['to']} at price {contract['price']}.\n"

        if bid_count > 0:
            average_bid_price = total_bid_price / bid_count
            summary += f"Average Bid Price: {average_bid_price:.2f}\n"
        if ask_count > 0:
            average_ask_price = total_ask_price / ask_count
            summary += f"Average Ask Price: {average_ask_price:.2f}\n"
        summary += f"Total Bids: {bid_count}, Total Asks: {ask_count}\n"

        # Add player balances and shares to the summary
        if self.user_number is not None:
            player_state = self.get_player_state(self.user_number)
            summary += (
                f"Player {self.user_number} Current State:\n"
                f"  Cash Available: {player_state['cash_available']}\n"
                f"  Cash Locked in Bids: {player_state['cash_locked_in_bids']}\n"
                f"  Shares Offered for Sale: {player_state['shares_offered_for_sale']}\n"
                f"  Shares Owned: {self.public_game_state.get(self.user_number, 0)}\n"
            )

        # Add summary of shares for all players
        summary += "Player Shares Summary:\n"
        for player_id, shares in self.public_game_state.items():
            summary += f"  Player {player_id}: {shares} shares\n"

        if self.verbose:
            print(f"Message Summary: {summary}")

        return summary

    def query_openai(self, summary):
        try:
            instructions = (
                "You are a trader in a double auction market. "
                "Based on the following market events and your current financial state, please respond with one of the following actions: "
                "'do nothing', 'bid X', 'ask Y', or 'cancel-order Z', where X, Y are values, and Z is an Order ID that needs to be cancelled. "
                "Also end your response with a reason with a | separator. "
                "Contract fulfilled cannot be canceled, so don't cancel-order for contract-fulfilled events. "
                "Your response should be in JSON format."
            )

            prompt = f"{instructions}\n\n{summary}"

            message = [{"role": "user", "content": prompt}]
            print(f"Querying OpenAI with the following prompt:\n{prompt}")

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=message,
            )

            response_text = response.choices[0].message.content
            print(f"LLM Response: {response_text}")

            ws_message = self.process_websocket_message(response_text)
            if ws_message:
                self.send_to_websocket_client(ws_message)

        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode OpenAI response JSON: {e}")
        except KeyError as e:
            logging.error(f"Key error in processing OpenAI response: {e}")
        except Exception as e:
            logging.error(f"Error communicating with OpenAI: {e}")

    def process_websocket_message(self, response_text):
        try:
            # Log the raw response to help with debugging
            # print(f"Raw LLM Response: {response_text}")

            # Check if the response is empty or just whitespace
            if not response_text.strip():
                logging.error("Received empty response from LLM")
                return None

            # Attempt to parse the JSON, stripping any leading or trailing whitespace
            response_data = json.loads(response_text.strip())

            # Extract action and reason from the parsed JSON
            action = response_data.get('action') or response_data.get(
                'response')
            reason = response_data.get('reason', '')

            if not action:
                logging.warning(
                    "LLM response is missing both 'action' and 'response' fields.")
                return None

            player_state = self.get_player_state(self.user_number)

            if action.lower().startswith('bid'):
                value = int(action.split()[1])
                if value <= player_state['cash_available']:
                    player_state['cash_locked_in_bids'] += value
                    player_state['cash_available'] -= value

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
                else:
                    logging.warning(
                        "LLM suggested a bid higher than available cash.")
                    return None
            elif action.lower().startswith('ask'):
                value = int(action.split()[1])
                if player_state['shares_available'] > 0:
                    player_state['shares_offered_for_sale'] += 1
                    player_state['shares_available'] -= 1

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
                else:
                    logging.warning(
                        "LLM suggested an ask but no shares are available.")
                    return None
            elif action.lower().startswith('cancel-order'):
                order_id = int(action.split()[1])
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
                    print(f"LLM suggested no action: {reason}")
                return None
            else:
                logging.warning(f"Unexpected action type from LLM: {action}")
                return None

            message_json = json.dumps(message)
            return message_json

        except json.JSONDecodeError as e:
            logging.error(
                f"Failed to parse LLM response as JSON: {e}\nResponse: {response_text}")
            return None
        except Exception as e:
            logging.error(
                f"Unexpected error in process_websocket_message: {e}")
            return None

    def update_player_wallet(self, data):
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
        self.dispatch_timer.cancel()

    def send_to_websocket_client(self, message):
        if self.websocket_client and hasattr(self.websocket_client.ws, 'send'):
            print(f"Message to send: {message}")
            try:
                self.websocket_client.ws.send(message)
            except Exception as e:
                logging.error(f"Error sending message to WebSocket client: {e}")
        else:
            if self.verbose:
                print(f"Message to send: {message}")
                print("WebSocket client is not available to send the message.")
