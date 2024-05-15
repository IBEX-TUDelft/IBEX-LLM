import json


class GameHandler:
    def __init__(self, game_id):
        self.messages = []
        self.game_id = game_id
        self.current_phase = None

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

    def call_llm_for_compensation_request(self, context):
        # Pseudo-code for calling the LLM
        # response = llm.generate_compensation_request(context)
        response = [None, 100000]  # Placeholder response
        return response

    def call_llm_for_compensation_offer(self, context):
        # Pseudo-code for calling the LLM
        # response = llm.generate_compensation_offer(context)
        response = [None, 75000]  # Placeholder response
        return response

    def call_llm_for_compensation_decision(self, context):
        # Pseudo-code for calling the LLM
        # response = llm.generate_compensation_decision(context)
        response = [0]  # Placeholder response
        return response

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
