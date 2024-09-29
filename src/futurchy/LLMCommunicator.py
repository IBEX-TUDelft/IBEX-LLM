import json
from openai import OpenAI
import logging
import re

class LLMCommunicator:
    def __init__(self):
        self.client = OpenAI()

    def query_openai(self, summary):
        try:
            instructions = (
                "You are an agent in a Harberger tax simulation. "
                "Based on the following events, please respond with an appropriate action. "
                "Your response should be in valid JSON format without any extra text, explanation, or formatting."
            )

            prompt = f"{instructions}\n\nEvents Summary:\n{summary}"
            logging.debug(f"Sending prompt to LLM: {prompt}")

            message = [{"role": "user", "content": prompt}]
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=message,
            )

            response_text = response.choices[0].message.content
            logging.debug(f"Received response from LLM: {response_text}")

            ws_message = self.process_websocket_message(response_text)
            return ws_message

        except Exception as e:
            logging.error(
                f"Error communicating with OpenAI: {e} (LLMCommunicator.query_openai)")
            return None

    def process_websocket_message(self, response_text):
        cleaned_response_text = None
        try:
            # Remove any extraneous formatting
            cleaned_response_text = response_text.strip().strip('```').strip()

            # Remove labels like "json" if they exist
            cleaned_response_text = re.sub(r'^json', '', cleaned_response_text,
                                           flags=re.IGNORECASE).strip()

            # Check if the response text is valid JSON
            response_json = json.loads(cleaned_response_text)
            return response_json

        except json.JSONDecodeError as e:
            logging.error(
                f"LLMCommunicator: Failed to decode JSON: {e} - Response text: {cleaned_response_text}")
            return None
        except Exception as e:
            logging.error(
                f"Error processing WebSocket message: {e} (LLMCommunicator.process_websocket_message)")
            return None

    def send_to_websocket_client(self, websocket_client, message):
        """
        Sends a message to the WebSocket client.

        Args:
            websocket_client: The WebSocket client to send the message to.
            message (str): The message to be sent.
        """
        if websocket_client:
            websocket_client.send_message(json.dumps(message))  # Ensure message is in JSON string format
        else:
            logging.error("WebSocket client not available.")