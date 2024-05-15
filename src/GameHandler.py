import json


class GameHandler:
    def __init__(self, game_id):
        self.messages = []
        self.game_id = game_id


    def handle_message(self, message):
        message_data = json.loads(message)
        self.messages.append(message_data)

        if message_data["type"] == "notice" and "Phase 3 has begun" in message_data["message"]:
            return {"gameId": self.game_id, "type": "compensation-request", "compensationRequests": [None, 100000]}
        elif message_data["type"] == "notice" and "Phase 4 has begun" in message_data["message"]:
            return {"gameId": self.game_id, "type": "compensation-offer", "compensationOffers": [None, 75000]}
        elif message_data["type"] == "notice" and "Phase 4 has begun" in message_data["message"]:
            return {"gameId": self.game_id, "type": "compensation-decision", "compensationDecisions": [0]}
        else:
            return {"summary": self.summarize_messages()}




