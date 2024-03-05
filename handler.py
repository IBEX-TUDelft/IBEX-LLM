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
                                         on_close=self.on_close)
        self.ws.on_open = self.on_open
        self.should_continue = True  # Flag to control the send_message loop
        self.wst = threading.Thread(target=self.ws.run_forever, daemon=True)

    def on_message(self, ws, message):
        """
        Callback executed when a message is received from the server.
        :param ws: Is the WebSocketApp instance that received the message.
        :param message: Is the message received from the server.
        :return:
        """
        print("Received:", message)

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

    def on_open(self, ws):
        """
        Callback executed when the connection is open.
        :param ws: Is the WebSocketApp instance that received the message.
        :return:
        """
        print("### Connection is open ###")
        threading.Thread(target=self.send_message, args=(ws,), daemon=True).start()

    def load_api_key(self):
        """
        Load the API key from an external file.
        """
        try:
            with open('token.txt',
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

        while self.should_continue:
            user_input = input(
                "Enter a message to send (type 'exit' to close): ")
            if user_input == 'exit':
                ws.close()
                break

            try:
                # Constructing the prompt for the OpenAI API
                # TODO: We need to modify this because its not right yet.
                prompt = f"You are a helpful assistant.\n\n{user_input}"

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

if __name__ == "__main__":
    websocket.enableTrace(False)
    client = WebSocketClient("ws://localhost:3088")
    client.run_forever()
