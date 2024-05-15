import websocket
import threading
import json
import re

class GameHandler:
    def __init__(self):
        self.messages = []

    def handle_message(self, message):
        message_data = json.loads(message)
        self.messages.append(message_data)

        if message_data["type"] == "notice" and "Phase 2 has begun" in message_data["message"]:
            return {"compensationRequest": [10000]}
        else:
            return {"summary": self.summarize_messages()}

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

class WebSocketClient:
    """
    A simple WebSocket client that sends a message to the server every second
    and prints the messages received from the server.

    The client is implemented using the websocket-client library, which is a
    WebSocket client for Python. The library can be installed using pip:

    @:param url: The URL of the WebSocket server to connect to.
    """
    def __init__(self, url, game_id, recovery):
        self.url = url
        self.game_id = game_id
        self.recovery = recovery
        self.game_handler = GameHandler()
        self.ws = websocket.WebSocketApp(url,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close,
                                         on_ping=self.on_ping,
                                         on_pong=self.on_pong)
        self.ws.on_open = self.on_open
        self.should_continue = True  # Flag to control the send_message loop
        self.wst = threading.Thread(target=lambda : self.ws.run_forever(ping_interval=30, ping_timeout=10), daemon=True)

    def on_message(self, ws, message):
        """
        Callback executed when a message is received from the server.
        :param ws: Is the WebSocketApp instance that received the message.
        :param message: Is the message received from the server.
        :return:
        """
        print("Received message:", message)  # Debugging: Print the received message
        try:
            action = self.game_handler.handle_message(message)
            if "compensationRequest" in action:
                response = json.dumps(action)
                print("Sending message:", response)  # Debugging: Print the message to be sent
                ws.send(response)
            else:
                print(action["summary"])
        except json.JSONDecodeError:
            print("Error decoding JSON from message:", message)

    def on_error(self, ws, error):
        """
        Callback executed when an error occurs.
        :param ws: Is the WebSocketApp instance that received the message.
        :param error: is the error that occurred.
        :return:
        """
        print("Error:", error)

    def on_close(self, ws):
        """
        Callback executed when the connection is closed.
        :param ws: Is the WebSocketApp instance that received the message.
        :return:
        """
        print("### closed ###")
        self.should_continue = False
        self.reconnect()

    def reconnect(self):
        """
        Function to reconnect to the server.
        :return:
        """
        self.wst = threading.Thread(target=self.ws.run_forever, daemon=True)
        self.wst.start()

    def on_open(self, ws):
        """
        Callback executed when the connection is open.
        :param ws: Is the WebSocketApp instance that received the message.
        :return:
        """
        print("### Connection is open ###")
        # Sending predefined message immediately upon connection
        initial_message = json.dumps({"gameId": self.game_id, "type": "join", "recovery": self.recovery})
        print("Sending message:", initial_message)  # Debugging: Print the message to be sent
        ws.send(initial_message)
        second_message = json.dumps({"gameId": self.game_id, "type": "player-is-ready"})
        print("Sending message:", second_message)  # Debugging: Print the message to be sent
        ws.send(second_message)
        # Start thread for user input to send messages
        threading.Thread(target=self.send_message, args=(ws,), daemon=True).start()

    def send_message(self, ws):
        """
        Function to send a message to the server.
        :param ws: Is the WebSocketApp instance that received the message.
        :return:
        """
        while self.should_continue:
            message = input("Enter a message to send (type 'exit' to close): ")
            if message == 'exit':
                ws.close()
                break
            print("Sending message:", message)  # Debugging: Print the message to be sent
            ws.send(message)

    def on_ping(self, ws, message):
        """
        Callback executed when a ping message is received from the server.
        :param ws: Is the WebSocketApp instance that received the message.
        :param message: Is the ping message received from the server.
        :return:
        """
        # print("Ping:", message)
        pass

    def on_pong(self, ws, message):
        """
        Callback executed when a pong message is received from the server.
        :param ws: Is the WebSocketApp instance that received the message.
        :param message: Is the pong message received from the server.
        :return:
        """
        # print("Pong:", message)
        pass

    def run_forever(self):
        """
        Function to start the WebSocket client and keep it running until the user
        :return:
        """
        self.wst.start()
        try:
            while self.wst.is_alive():
                self.wst.join(timeout=1)
        except KeyboardInterrupt:
            self.ws.close()

def parse_url(url):
    """
    Parse the URL to extract the gameId and recovery token.
    :param url: The URL to parse.
    :return: A tuple containing the gameId and recovery token.
    """
    match = re.search(r'/voting/(\d+)/(\w+)', url)
    if match:
        game_id = int(match.group(1))
        recovery = match.group(2)
        return game_id, recovery
    else:
        raise ValueError("URL format is incorrect. Expected format: http://localhost:8080/voting/<gameId>/<recovery>")

if __name__ == "__main__":
    # websocket.enableTrace(False)
    url_input = input("Enter the URL: ")
    try:
        game_id, recovery = parse_url(url_input)
        client = WebSocketClient("ws://localhost:3088", game_id, recovery)
        client.run_forever()
    except ValueError as e:
        print(e)
