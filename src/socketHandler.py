import websocket
import threading
import json
import openai

class WebSocketClient:
    """
    A simple WebSocket client that sends a message to the server every second
    and prints the messages received from the server.

    The client is implemented using the websocket-client library, which is a
    WebSocket client for Python. The library can be installed using pip:

    @:param url: The URL of the WebSocket server to connect to.
    """
    def __init__(self, url):
        self.url = url
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
        try:
            msg_data = json.loads(message)
            # Define a set of eventTypes to ignore
            ignore_event_types = {
                "assign-name", "phase-instructions",
                "set-timer", "reset-timer", "phase-transition", "round-end", "ready-received"
            }
            # Check if the message should be ignored
            if msg_data.get("type") == "event" and msg_data.get("eventType") in ignore_event_types:
                return  # Ignore these event types
            if msg_data.get("type") == "info" and ("rejoined the game" in msg_data.get("message", "") or "joined. We have now" in msg_data.get("message", "")):
                return  # Ignore these info messages

            # If the message wasn't ignored, print it
            print("Received:", message)
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
        print("### Connection is open ###")

        # Sending initial game-specific messages
        initial_message = '{"gameId":16,"type":"join","recovery":"q3yrymy6y8ixicjlq241nswpi00ag74deooxedsgg0so78b5iipr6ol85v4milq0"}'
        ws.send(initial_message)
        print("Sent initial game join message.")

        second_message = '{"gameId":16,"type":"player-is-ready"}'
        ws.send(second_message)
        print("Sent player is ready message.")

        # Start thread for handling incoming WebSocket messages
        threading.Thread(target=self.send_message, args=(ws,),
                         daemon=True).start()

    def load_api_key(self):
        """
        Load the API key from an external file.
        """
        try:
            with open('../config/token.txt',
                      'r') as file:  # Update the path to your actual file location
                return file.read().strip()
        except FileNotFoundError:
            print("API key file not found. Please check the file path.")
            exit()


    def send_message(self, ws):
        """
        Function to send a message to the server.
        :param ws: Is the WebSocketApp instance that received the message.
        :return:
        """
        openai.api_key = self.load_api_key()

        print("Waiting for instructions...")

        while self.should_continue:
            user_input = input(
                "Enter a message to send (type 'exit' to close): ")
            if user_input == 'exit':
                ws.close()
                break

            try:
                print("Calling OpenAI API...")
                # Constructing the prompt for the OpenAI API
                # TODO: We need to modify this because its not right yet.
                prompt = f"You are an intelligent agent participating in a simulation. Wait for instructions."

                # Requesting a completion from OpenAI
                response = openai.completions.create(
                    model="gpt-3.5-turbo",
                    prompt=prompt,
                    temperature=0.5,
                    max_tokens=150
                )

                # Extracting the text response
                text_response = response.choices[0].text.strip()

                print("AI Response:", text_response)

                # Sending the AI response over WebSocket (or modify as needed)
                ws.send(text_response)
            except Exception as e:
                print(f"Error while calling OpenAI API: {e}")

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


    def on_ping(self, ws, message):
        """
        Callback executed when a ping message is received from the server.
        :param ws: Is the WebSocketApp instance that received the message.
        :param message: Is the ping message received from the server.
        :return:
        """
        # TODO: Check if the ping message is received and if the connection is still alive, otherwise do a comedown should be reset to the beginning.
        # print("Ping:", message)


    def on_pong(self, ws, message):
        """
        Callback executed when a pong message is received from the server.
        :param ws: Is the WebSocketApp instance that received the message.
        :param message: Is the pong message received from the server.
        :return:
        """
        # print("Pong:", message)

if __name__ == "__main__":
    websocket.enableTrace(False)
    client = WebSocketClient("ws://localhost:3088")
    client.run_forever()
