import logging
import json
from openai import OpenAI

class GameHandler:
    def __init__(self, game_id, verbose=False):
        self.messages = []
        self.game_id = game_id
        self.current_phase = None
        self.client = OpenAI()
        self.verbose = verbose
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
        message_data = json.loads(message)
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

        # If no special handling is needed, just return a summary
        return {"summary": self.summarize_messages()}

    def prepare_compensation_request(self):
        context = self.summarize_messages()
        compensation_request = self.request_compensation_from_llm(context, "request")
        return {"gameId": self.game_id, "type": "compensation-request", "compensationRequests": compensation_request}

    def prepare_compensation_offer(self):
        context = self.summarize_messages()
        compensation_offer = self.request_compensation_from_llm(context, "offer")
        return {"gameId": self.game_id, "type": "compensation-offer", "compensationOffers": compensation_offer}

    def prepare_compensation_decision(self):
        context = self.summarize_messages()
        compensation_decision = self.request_compensation_from_llm(context, "decision")
        return {"gameId": self.game_id, "type": "compensation-decision", "compensationDecisions": compensation_decision}

    def request_compensation_from_llm(self, context, action_type):
        if self.verbose:
            print(f"Requesting compensation from LLM for {action_type}: {context}")
        logging.debug(f"Sending message to LLM: {context}")
        try:
            # Building the message for LLM
            message = [
                {"role": "user", "content": context},
            ]
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=message,
            )
            if self.verbose:
                print(f"LLM response: {response}")

        except Exception as e:
            logging.error(f"Error sending message to LLM: {e}")
            return None

    def summarize_messages(self):
        summaries = []
        for msg in self.messages:
            if msg["type"] == "event":
                if msg["eventType"] == "assign-role":
                    summaries.append(f"Assigned role: {msg['data']['tag']} with property {msg['data']['property']['name']}.")
                elif msg["eventType"] == "players-known":
                    summaries.append(f"Known players: {', '.join([player['tag'] for player in msg['data']['players']])}.")
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
