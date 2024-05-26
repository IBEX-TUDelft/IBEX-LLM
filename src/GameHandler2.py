import logging
import json
import openai

class GameHandler:
    def __init__(self, game_id):
        self.messages = []
        self.game_id = game_id
        self.current_phase = None
        openai.api_key = self.load_api_key()


    def load_api_key(self):
        try:
            with open('../config/token.txt', 'r') as file:
                return file.read().strip()
        except FileNotFoundError:
            print("API key file not found. Please check the file path.")
            exit()

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
        # Prepare the context for the LLM
        context = self.generate_context()
        # Call the LLM to get the compensation request (pseudo-code)
        compensation_request = self.call_llm_for_compensation_request(context)
        return {"gameId": self.game_id, "type": "compensation-request", "compensationRequests": compensation_request}

    def prepare_compensation_offer(self):
        # Prepare the context for the LLM
        context = self.generate_context()
        # Call the LLM to get the compensation offer (pseudo-code)
        compensation_offer = self.call_llm_for_compensation_offer(context)
        return {"gameId": self.game_id, "type": "compensation-offer", "compensationOffers": compensation_offer}

    def prepare_compensation_decision(self):
        # Prepare the context for the LLM
        context = self.generate_context()
        # Call the LLM to get the compensation decision (pseudo-code)
        compensation_decision = self.call_llm_for_compensation_decision(context)
        return {"gameId": self.game_id, "type": "compensation-decision", "compensationDecisions": compensation_decision}

    def generate_context(self):
        # Generate a context string or object based on the message history
        context = {
            "game_id": self.game_id,
            "current_phase": self.current_phase,
            "messages": self.messages
        }
        return context

    def parse_compensation_request(self, response):
        if 'amount' in response and 'details' in response:
            return [response['details'], response['amount']]
        return [None, 100000]  # Fallback values

    def parse_compensation_offer(self, response):
        if 'offer' in response:
            return [response['offer']['details'], response['offer']['amount']]
        return [None, 75000]  # Fallback values

    def parse_compensation_decision(self, response):
        if 'decision' in response:
            return [response['decision']]
        return [0]  # Fallback decision

    def call_llm_for_compensation_request(self, context):
        content = json.dumps(context)
        response = self.send_message_to_llm(content, "compensation-request")
        return self.parse_compensation_request(response) if response else [
            None, 100000]

    def call_llm_for_compensation_offer(self, context):
        content = json.dumps(context)
        response = self.send_message_to_llm(content, "compensation-offer")
        return self.parse_compensation_offer(response) if response else [None,
                                                                         75000]

    def call_llm_for_compensation_decision(self, context):
        content = json.dumps(context)
        response = self.send_message_to_llm(content, "compensation-decision")
        return self.parse_compensation_decision(response) if response else [0]

    def send_message_to_llm(self, content, role):
        try:
            # Building the message for LLM
            message = {
                "role": role,
                "content": content,
            }
            logging.debug(f"Sending message to LLM: {message}")
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[message],
            )
            print(f"LLM response: {response.choices[0].message['content']}")

            return response.choices[0].message['content']
        except Exception as e:
            logging.error(f"Error sending message to LLM: {e}")
            return None

    def summarize_messages(self):
        # TODO: Implement a more detailed summary based on the message history
        # TODO: Summarization model, but not to the needs of losing throughput.
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
