import json
from openai import OpenAI
import logging

class LLMCommunicator:
    def __init__(self):
        self.client = OpenAI()

    def query_openai(self, summary):
        """
        Sends the summarized query to the LLM agent with instructions.

        Args:
            summary (str): The summarized query to be sent.
        """
        try:
            instructions = (
                "You are an agent in a Harberger tax simulation. "
                "Based on the following events, please respond with an appropriate action."
                "Your response should be in JSON format."
            )

            prompt = f"{instructions}\n\nEvents Summary:\n{summary}"

            message = [{"role": "user", "content": prompt}]
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=message,
            )

            response_text = response.choices[0].message.content
            print(f"response: {response_text}")


            ws_message = self.process_websocket_message(response_text)
            return ws_message

        except Exception as e:
            logging.error(f"Error communicating with OpenAI: {e}")
            return None

    def process_websocket_message(self, response_text):
        """
        Processes the response text from the LLM agent and generates the appropriate WebSocket message.

        Args:
            response_text (str): The response text from the LLM agent.

        Returns:
            str: The WebSocket message to be sent.
        """
        try:
            response_data = json.loads(response_text)
            if response_data.get('type') == 'message':
                message = response_data.get('content', '')
                if message:
                    return message

        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode response JSON: {e}")
        except Exception as e:
            logging.error(f"Unexpected error in process_websocket_message: {e}")

        return None

    def send_to_websocket_client(self, websocket_client, message):
        """
        Sends a message to the WebSocket client.

        Args:
            websocket_client: The WebSocket client to send the message to.
            message (str): The message to be sent.
        """
        if websocket_client:
            websocket_client.send_message(message)
        else:
            logging.error("WebSocket client not available.")