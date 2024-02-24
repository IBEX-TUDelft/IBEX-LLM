import websocket
import threading

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
            ws.send(message)

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
