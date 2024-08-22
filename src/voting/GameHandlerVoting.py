import logging
import json
import re
import time
from openai import OpenAI


class GameHandler:
    def __init__(self, game_id, verbose=False):
        self.messages = []
        self.game_id = game_id
        self.current_phase = 1
        self.client = OpenAI()
        self.verbose = verbose
        self.boundaries = {}
        self.send_initial_message()

    def send_initial_message(self):
        initial_message = {
            "role": "system",
            "content": "You are participating in a voting simulation."
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

    def handle_message(self, message):
        try:
            message_data = json.loads(message)
        except json.JSONDecodeError:
            logging.error(f"Error decoding JSON from message: {message}")
            return None

        self.messages.append(message_data)

        # Determine the current phase from the message
        if message_data["type"] == "notice":
            if "Phase 3 has begun" in message_data["message"]:
                self.current_phase = 3
                return self.prepare_compensation_request()
            elif "Phase 4 has begun" in message_data["message"]:
                self.current_phase = 4
                return self.prepare_compensation_offer()
            elif "Phase 6 has begun" in message_data["message"]:
                self.current_phase = 6
                return self.prepare_compensation_decision()

        elif message_data["type"] == "event":
            if message_data["eventType"] == "assign-role":
                self.store_boundaries(message_data["data"])

        if message_data["type"] == "event" and message_data[
            "eventType"] == "phase-transition":
            if message_data["data"]["phase"] == 0:
                print("Phase 0 has begun. Sending player-is-ready message.")
                return {"gameId": self.game_id, "type": "player-is-ready"}

        # If no special handling is needed, just return a summary
        return {"summary": self.summarize_messages()}

    def store_boundaries(self, data):
        property_name = data["property"]["name"]
        self.boundaries[property_name] = data["boundaries"]

        if self.verbose:
            print(
                f"Boundaries stored for {property_name}: {self.boundaries[property_name]}")

    def prepare_compensation_request(self):
        context = self.generate_context("request")
        compensation_request = self.request_compensation_from_llm(context,
                                                                  "request")
        return {"gameId": self.game_id, "type": "compensation-request",
                "compensationRequests": compensation_request}

    def prepare_compensation_offer(self):
        context = self.generate_context("offer")
        compensation_offer = self.request_compensation_from_llm(context,
                                                                "offer")
        return {"gameId": self.game_id, "type": "compensation-offer",
                "compensationOffers": compensation_offer}

    def prepare_compensation_decision(self):
        context = self.generate_context("decision")
        compensation_decision = self.request_compensation_from_llm(context,
                                                                   "decision")
        return {"gameId": self.game_id, "type": "compensation-decision",
                "compensationDecisions": compensation_decision}

    def generate_context(self, action_type):
        property_name = next(
            iter(self.boundaries))  # Get the first property name
        boundaries = self.boundaries.get(property_name, {})

        if action_type in ["request", "offer"]:
            if "owner" in boundaries and "projectA" in boundaries["owner"]:
                low, high = boundaries["owner"]["projectA"]["low"], \
                boundaries["owner"]["projectA"]["high"]
                context = f"Provide a {action_type} in the format 'compensation-{action_type}: X' where X is an integer between {low} and {high}."
            else:
                raise ValueError(
                    f"Invalid boundaries for property: {property_name}")
        elif action_type == "decision":
            context = "Provide a decision in the format 'compensation-decision: X' where X is 0 or 1."

        if self.verbose:
            print(f"Generated context for {action_type}: {context}")

        return context

    def request_compensation_from_llm(self, context, action_type):
        if self.verbose:
            print(
                f"Requesting compensation from LLM for {action_type}: {context}")
        logging.debug(f"Sending message to LLM: {context}")
        try:
            message = [
                {"role": "user", "content": context},
            ]
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=message,
            )
            response_text = response.choices[0].message.content
            if self.verbose:
                print(f"LLM response: {response_text}")

            return self.extract_integer_from_response(response_text,
                                                      action_type)

        except Exception as e:
            logging.error(f"Error sending message to LLM: {e}")
            return None

    def extract_integer_from_response(self, response, action_type):
        match = re.search(r'\b\d+\b', response)
        if match:
            value = int(match.group())
            if action_type in ["request", "offer"]:
                property_name = next(
                    iter(self.boundaries))  # Get the first property name
                boundaries = self.boundaries.get(property_name, {})
                if boundaries and "owner" in boundaries and "projectA" in \
                        boundaries["owner"]:
                    low, high = boundaries["owner"]["projectA"]["low"], \
                    boundaries["owner"]["projectA"]["high"]
                    if low <= value <= high:
                        return value
            elif action_type == "decision":
                if value in [0, 1]:
                    return value
        return None

    def summarize_messages(self):
        summaries = []
        for msg in self.messages:
            if msg["type"] == "event":
                if msg["eventType"] == "assign-role":
                    summaries.append(
                        f"Assigned role: {msg['data']['tag']} with property {msg['data']['property']['name']}.")
                elif msg["eventType"] == "players-known":
                    summaries.append(
                        f"Known players: {', '.join([player['tag'] for player in msg['data']['players']])}.")
                elif msg["eventType"] == "compensation-offer-made":
                    summaries.append("Compensation offer made.")
                elif msg["eventType"] == "final-profit":
                    summaries.append(
                        f"Final profit information received. Condition: {msg['data']['condition']}, "
                        f"Tally: {msg['data']['tally']}, Value: {msg['data']['value']}, Compensation: {msg['data']['compensation']}."
                    )
                elif msg["eventType"] == "round-summary":
                    summaries.append(
                        f"Round {msg['data']['round']} summary. Condition: {msg['data']['condition']}, Value: {msg['data']['value']}, "
                        f"Tally: {msg['data']['tally']}, Compensation: {msg['data']['compensation']}, Profit: {msg['data']['profit']}."
                    )
            elif msg["type"] == "notice":
                summaries.append(msg["message"])

        return " ".join(summaries)

    def process_websocket_message(self, message):
        try:
            action = self.handle_message(message)
            if action is not None and isinstance(action, dict):
                if any(key in action for key in
                       ["compensationOffers", "compensationRequests",
                        "compensationDecisions"]) or action.get(
                        'type') == 'player-is-ready':
                    response = json.dumps(action)
                    if self.verbose:
                        print(
                            "Processed WebSocket message, prepared response:",
                            response)
                    if action.get('type') == 'player-is-ready':
                        time.sleep(5)
                    return response
        except Exception as e:
            print("Unexpected error:", e)
        return None
