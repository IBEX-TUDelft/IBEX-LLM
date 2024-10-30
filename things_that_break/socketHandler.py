import websocket
import threading
import json
import openai
from time import sleep

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
        openai.api_key = self.load_api_key()
        self.get_latest_message = None
        self.get_instruction_message = None



    def on_message(self, ws, message):
        """
        Callback executed when a message is received from the server.
        :param ws: Is the WebSocketApp instance that received the message.
        :param message: Is the message received from the server.
        :return:
        """
        try:
            msg_data = json.loads(message)
            # Filter based on eventType; only process if eventType matches our criteria
            eventType = msg_data.get('eventType')
            if eventType in ['introduction-instructions', 'action-required', 'assign-role', 'players-known']:
                # Process the message as needed
                self.get_latest_message = self.instruction_to_prompt(message)
        except json.JSONDecodeError:
            print("Error decoding JSON from message:", message)


    def instruction_to_prompt(self, instruction):
        """
        Function to convert an instruction to a prompt for the AI.
        :param instruction: The instruction to convert to a prompt.
        :return: The prompt to use for the AI.
        """
        try:
            # Decode the JSON message to access its contents
            msg_data = json.loads(instruction)
            eventType = msg_data.get("eventType")

            if eventType == "introduction-instructions":
                # Extract and format the introduction instructions
                instructions = msg_data.get("data", {}).get("data", {})
                welcome_message = instructions.get("welcomeMessage", "")
                role_assignment = instructions.get("roleAssignment", "")
                response_timing = instructions.get("responseTiming", "")
                response_format = instructions.get("responseFormat", "")
                example = instructions.get("example", {}).get("instructions",
                                                              "")
                additional_info = instructions.get("example", {}).get(
                    "additionalInfo", "")

                content = f"{welcome_message} {role_assignment} {response_timing} {response_format} Example: {example} {additional_info}"

                return json.dumps({
                    "role": "system",
                    "content": content
                }, indent=2)

            # Handle action-required messages
            elif eventType == "action-required":
                # Extract the nested 'data' containing the actual instructions
                instructions = msg_data.get("data", {}).get("data", {})

                # Construct the prompt for action-required messages
                action_type = instructions.get("actionType", "")
                detailed_instructions = instructions.get("instructions", "")
                response_format = instructions.get("format", "")
                action_required_by = instructions.get("actionRequiredBy", "")
                deadline = instructions.get("deadline", "")
                additional_info = instructions.get("additionalInfo", "")

                content = (
                    f"Action Type: {action_type}\n"
                    f"Instructions: {detailed_instructions}\n"
                    f"Response Format: {response_format}\n"
                    f"Action Required By: {action_required_by}\n"
                    f"Deadline: {deadline}\n"
                    f"Additional Information: {additional_info}"
                )

                return json.dumps({
                    "role": "user",
                    "content": content
                }, indent=2)

            # Handle assign-role messages
            elif eventType == "assign-role":
                # Extract the 'data' dictionary which contains the role and other information
                data = msg_data.get("data", {})

                role = data.get("role", "N/A")  # Default to "N/A" if not found
                property_name = data.get("property", {}).get("name",
                                                             "No Property")  # Example of accessing nested data
                owner_id = data.get("property", {}).get("owner", "No Owner ID")
                boundaries = data.get("boundaries", {})

                # Constructing a detailed content string with the extracted information
                content = (
                    f"Your role is: {role}\n"
                    f"Property Name: {property_name}\n"
                    f"Owner ID: {owner_id}\n"
                    f"Boundaries: {boundaries}"
                )

                return json.dumps({
                    "role": "system",
                    "content": content
                }, indent=2)


            else:
                # Handle unexpected eventType
                return json.dumps({
                    "role": "system",
                    "content": f"Received an unhandled eventType: {eventType}"
                }, indent=2)

        except json.JSONDecodeError:
            return json.dumps({
                "role": "system",
                "content": "Error decoding instruction message."
            }, indent=2)

    def instruction_reader(self):
        """
        Processes instructions from a DOCX file, converts them to JSON, and then formats them for the OpenAI API.
        """
        json_path = '../data/processed/instructions.json'

        # Reading the saved JSON instructions
        with open(json_path, 'r') as file:
            instructions_json = json.load(file)

        # Transforming the JSON to the OpenAI API format
        formatted_instructions = self.json_to_openai_format(instructions_json)
        # print(f"Formatted instructions: {formatted_instructions}")
        self.get_instruction_message = formatted_instructions

    def json_to_openai_format(self, json_obj):
        """
        Transforms the JSON object into a format compatible with OpenAI's API.

        Args:
            json_obj: The JSON object containing the instruction sections.

        Returns:
            A dictionary with "role": "user" and "content": concatenated instructions.
        """
        content = []
        for section, texts in json_obj.items():
            # For each section, join its text and append to the content list
            section_content = ' '.join(texts)
            content.append(f"{section}: {section_content}")

        # Join all section contents into a single string
        content_str = "\n\n".join(content)

        # Return the formatted dictionary for OpenAI API
        return {"role": "user", "content": content_str}


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
        # Ensure the existing WebSocket connection is closed before attempting to reconnect
        if self.ws:
            self.ws.close()
        self.ws = websocket.WebSocketApp(self.url,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close)
        self.wst = threading.Thread(
            target=lambda: self.ws.run_forever(ping_interval=30,
                                               ping_timeout=10), daemon=True)
        self.wst.start()

    def on_open(self, ws):
        print("### Connection is open ###")

        # Sending initial game-specific messages
        initial_message = '{"gameId":15,"type":"join","recovery":"q3yrymy6y8ixicjlq241nswpi00ag74deooxedsgg0so78b5iipr6ol85v4milq0"}'
        ws.send(initial_message)
        print("Sent initial game join message.")

        second_message = '{"gameId":15,"type":"player-is-ready"}'
        ws.send(second_message)
        print("Sent player is ready message.")

        ws.send('{"gameId":15,"type":"join","recovery":"mei5p7p4ht1pdkdg876t2qsbj4kma5py7rhl4uvr3f3whatv71f922zhzrpij1q0"}')
        ws.send('{"gameId":15,"type":"player-is-ready"}')

        # Start thread for handling incoming WebSocket messages
        threading.Thread(target=self.send_message, args=(ws,),
                         daemon=True).start()

    def load_api_key(self):
        """
        Load the API key from an external file.
        """
        try:
            with open('/config/token.txt',
                      'r') as file:
                return file.read().strip()
        except FileNotFoundError:
            print("API key file not found. Please check the file path.")
            exit()

    def send_message(self, ws):
        print("Waiting for instructions...")
        while self.should_continue:
            if self.get_latest_message:
                prompt = json.loads(self.get_latest_message)
                if self.get_instruction_message:
                    prompt = [prompt, self.get_instruction_message]
                    response = openai.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=prompt,
                    )
                    self.get_instruction_message = None
                else:
                    response = openai.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[prompt],
                    )
                print(f"prompt: {prompt}")


                # Extracting the text response
                ai_response = response.choices[0].message.content.strip()

                print("AI Response:", ai_response)

                # Sending the JSON-formatted response
                ws.send(ai_response)

                # Reset the get_latest_message to prevent duplicate processing
                self.get_latest_message = None

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
    client.instruction_reader()
    client.run_forever()


