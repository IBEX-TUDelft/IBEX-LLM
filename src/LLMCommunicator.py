import json
from openai import OpenAI
import logging
import re

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


            ws_message = self.process_websocket_message(response_text)
            return ws_message

        except Exception as e:
            logging.error(f"Error communicating with OpenAI: {e} (LLMCommunicator.query_openai)")
            return None

    def process_websocket_message(self, response_text):
        """
        Processes the response text from the LLM agent and generates the appropriate WebSocket message.

        Args:
            response_text (str): The response text from the LLM agent.

        Returns:
            str: The WebSocket message to be sent.

        """
        cleaned_response_text = None
        try:
            # Remove the triple backticks and any leading or trailing whitespace
            cleaned_response_text = response_text.strip().strip('```').strip()

            # Remove the "json" label if it exists
            if cleaned_response_text.startswith("json"):
                cleaned_response_text = cleaned_response_text[
                                        len("json"):].strip()

            # Attempt to parse the cleaned JSON
            response_json = json.loads(cleaned_response_text)

            if response_json:
                return response_json
            else:
                logging.error("Message field not found in the response JSON.")
                return None

        except json.JSONDecodeError as e:
            logging.error(
                f"Failed to decode JSON: {e} - Response text: {cleaned_response_text}")
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
            print(f"Sending to WS: {message}")
            websocket_client.send_message(message)
        else:
            logging.error("WebSocket client not available.")