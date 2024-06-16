import json

class GameHandler:
    def __init__(self, game_id, verbose=True):
        self.messages = []
        self.game_id = game_id
        self.verbose = verbose

    def handle_message(self, message):
        # Convert message string to dictionary if needed
        if isinstance(message, str):
            message_data = json.loads(message)
        else:
            message_data = message

        # Log the message if verbose mode is on
        if self.verbose:
            print("Received message:", message_data)

        self.messages.append(message_data)
        # Process and respond based on message type
        return self.process_message(message_data)

    def process_message(self, message_data):
        # Handle different types of messages based on 'type' and 'eventType'
        msg_type = message_data.get('type')
        if msg_type == 'event':
            return self.handle_event(message_data['eventType'], message_data['data'])
        return {"status": "Unhandled message type"}

    def handle_event(self, event_type, data):
        # Dispatch event handling to specific methods
        handler = {
            'add-order': self.add_order,
            'delete-order': self.delete_order,
            'asset-movement': self.asset_movement,
            'contract-fulfilled': self.contract_fulfilled
        }.get(event_type, self.unhandled_event)

        return handler(data)

    def add_order(self, data):
        # Log or process an order addition
        if self.verbose:
            print("Adding order:", data)
        return {"gameId": self.game_id, "type": "add-order", "data": data}

    def delete_order(self, data):
        # Log or process an order deletion
        if self.verbose:
            print("Deleting order:", data)
        return {"gameId": self.game_id, "type": "delete-order", "data": data}

    def asset_movement(self, data):
        # Handle asset purchase or sale
        if self.verbose:
            print("Asset movement:", data)
        return {"gameId": self.game_id, "type": "asset-movement", "data": data}

    def contract_fulfilled(self, data):
        # Process a completed contract
        if self.verbose:
            print("Contract fulfilled:", data)
        return {"gameId": self.game_id, "type": "contract-fulfilled", "data": data}

    def unhandled_event(self, data):
        # Handle any unprocessed or unknown events
        if self.verbose:
            print("Unhandled event:", data)
        return {"status": "Unhandled event type", "data": data}

    def send_message(self, message):
        # Simulate sending a message
        message_str = json.dumps(message)
        if self.verbose:
            print("Sending message:", message_str)
        self.messages.append(message)