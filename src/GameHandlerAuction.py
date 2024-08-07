import json
from openai import OpenAI
import logging


class GameHandler:
    def __init__(self, game_id, verbose=False):
        self.game_id = game_id
        self.players = {}
        self.orders = {}
        self.events = []
        self.current_phase = 1
        self.current_round = 1
        self.client = OpenAI()
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

        if event_type in ['add-order', 'delete-order', 'asset-movement',
                          'contract-fulfilled']:
            self.query_openai(event_type, data)

    def handle_error(self, error_data):
        logging.error(f"Game error: {error_data['message']}")

    def handle_notice(self, notice_data):
        logging.info(f"Game notice: {notice_data['message']}")


    def query_openai(self, event_type, data):
        try:
            # Prepare a context or prompt for OpenAI based on the event and data
            prompt = self.prepare_prompt(event_type, data)
            print(f"Querying OpenAI for event: {event_type} with prompt: {prompt}")
            message = [{"role": "user", "content": prompt}]

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=message,
            )
            self.process_openai_response(response, event_type, data)
        except Exception as e:
            logging.error(f"Error communicating with OpenAI: {e}")

    def prepare_prompt(self, event_type, data):
        if event_type == 'add-order':
            return f"A new order has been added with price {data['order']['price']} and quantity {data['order']['quantity']}. How should the market react?"
        elif event_type == 'delete-order':
            return "An order has been deleted. How should the market adjust?"
        elif event_type == 'asset-movement':
            return f"An asset movement occurred with a total value of {data['movement']['total']}. What are the implications?"
        return "What should happen next in the game?"

    def process_openai_response(self, response, event_type, data):
        response_text = response.choices[0].message.content
        print(f"OpenAI Response: {response_text}")
        # Here you can add logic to update game state based on response

    def process_websocket_message(self, message):
        self.process_message(message)
        # Here you could format a response message and send it back to the server if needed


