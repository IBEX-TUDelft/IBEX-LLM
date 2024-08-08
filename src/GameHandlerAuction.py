import json
import time
import random
from openai import OpenAI
import logging

class GameHandler:
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
        elif event_type == 'error':
            self.handle_error(message_data)
        elif event_type == 'notice':
            self.handle_notice(message_data)

    def handle_event(self, event_data):
        event_type = event_data['eventType']
        data = event_data['data']

        if event_type == 'player-joined':
            self.update_player_wallet(data)

        if event_type in ['add-order', 'delete-order', 'asset-movement', 'contract-fulfilled']:
            self.update_message_stack(event_type, data)
            self.query_openai(event_type, data)

    def handle_error(self, error_data):
        logging.error(f"Game error: {error_data['message']}")

    def handle_notice(self, notice_data):
        logging.info(f"Game notice: {notice_data['message']}")

    def update_player_wallet(self, data):
        self.player_wallet = data['wallet']
        if self.verbose:
            print(f"Updated player wallet: {self.player_wallet}")

    def update_message_stack(self, event_type, data):
        self.message_stack.append({'event_type': event_type, 'data': data})
        if self.verbose:
            print(f"Updated message stack: {self.message_stack}")

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
            if self.verbose:
                print(f"Reaction time: {reaction_time:.2f} seconds")

            time.sleep(self.fixed_wait_time)
            self.fixed_wait_time = random.uniform(1, 5)

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
        print(f"OpenAI Response: {response_text}")
        # Here we can add logic to update game state based on response

    def process_websocket_message(self, message):
        self.process_message(message)


# Initialize the GameHandler
handler = GameHandler(game_id=308, verbose=True)

# Define the example messages
messages = [
    '{"type":"event","eventType":"player-joined","data":{"authority":"admin","number":0,"shares":1,"cash":100,"wallet":{"balance":100,"shares":1},"gameId":305,"role":0}}',
    '{"type":"event","eventType":"add-order","data":{"order":{"id":1,"sender":1,"price":5,"quantity":1,"type":"ask"}}}',
    '{"type":"event","eventType":"add-order","data":{"order":{"id":2,"sender":1,"price":5,"quantity":1,"type":"bid"}}}',
    '{"type":"event","eventType":"contract-fulfilled","data":{"from":2,"to":1,"price":5,"buyerFee":0,"sellerFee":0,"median":5}}',
    '{"type":"event","eventType":"delete-order","data":{"order":{"id":2,"type":"bid"}}}',
    '{"type":"event","eventType":"add-order","data":{"order":{"id":3,"sender":2,"price":3,"quantity":1,"type":"bid"}}}',
    '{"type":"event","eventType":"contract-fulfilled","data":{"from":1,"to":2,"price":3,"buyerFee":0,"sellerFee":0,"median":4}}',
    '{"type":"event","eventType":"delete-order","data":{"order":{"id":3,"type":"bid"}}}',
    '{"type":"event","eventType":"add-order","data":{"order":{"id":4,"sender":1,"price":4,"quantity":1,"type":"bid"}}}',
    '{"type":"event","eventType":"contract-fulfilled","data":{"from":1,"to":2,"price":5,"buyerFee":0,"sellerFee":0,"median":5}}',
    '{"type":"event","eventType":"delete-order","data":{"order":{"id":1,"type":"ask"}}}',
    '{"type":"event","eventType":"contract-fulfilled","data":{"from":2,"to":1,"price":4,"buyerFee":0,"sellerFee":0,"median":4.5}}',
    '{"type":"event","eventType":"delete-order","data":{"order":{"id":4,"type":"bid"}}}'
]

# Simulate receiving the messages
for msg in messages:
    handler.process_websocket_message(msg)

# Example usage
if __name__ == "__main__":
    handler = GameHandler(game_id=308, verbose=True)
    for msg in messages:
        handler.process_websocket_message(msg)