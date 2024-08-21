import json
import threading
from queue import Queue
import logging
from LLMCommunicator import LLMCommunicator

class GameHandler:
    def __init__(self, game_id, websocket_client=None, verbose=False):
        self.game_id = game_id
        self.verbose = verbose
        self.message_queue = Queue(maxsize=20)
        self.dispatch_interval = 10
        self.player_wallet = {}
        self.user_number = None
        self.user_role = None
        self.current_phase = 1
        self.current_round = 1
        self.websocket_client = websocket_client
        self.roles = {}
        self.properties = {}

        # Start the dispatch timer
        self.dispatch_timer = threading.Timer(self.dispatch_interval, self.dispatch_summary)
        self.dispatch_timer.start()

        # Can be found in LLMCommunicator.py
        self.llm_communicator = LLMCommunicator()

    def receive_message(self, message):
        try:
            message_data = json.loads(message)
            event_type = message_data.get('eventType', '')

            if event_type == 'assign-name':
                self.user_number = message_data['data']['number']
            elif event_type == 'players-known':
                self.handle_players_known(message_data['data']['players'])
            elif event_type == 'assign-role':
                self.handle_assign_role(message_data['data'])
            elif event_type == 'phase-transition':
                self.handle_phase_transition(message_data['data'])
            else:
                self.message_queue.put((2, message))  # Default priority

            if self.verbose:
                print(f"Message received: {message}")

        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode message JSON: {e}")
        except Exception as e:
            logging.error(f"Unexpected error in receive_message: {e}")

    def handle_players_known(self, players):
        role_map = {1: "Speculator", 2: "Developer", 3: "Owner"}
        for player in players:
            number = player['number']
            role_number = player['role']
            role_name = role_map.get(role_number, "Unknown")
            self.roles[number] = role_name
            if number == self.user_number:
                self.user_role = role_name
        if self.verbose:
            print(f"Player roles known: {self.roles}")

    def handle_assign_role(self, data):
        try:
            role = data['role']
            self.user_role = role
            if self.verbose:
                print(f"User assigned role: {self.user_role}")

            # Additional logic to handle wallet, property, and other data
            self.update_player_wallet(data.get('wallet'))
            self.properties[self.user_number] = data.get('property', {})

        except KeyError as e:
            logging.error(f"Missing key in handle_assign_role: {e}")

    def update_player_wallet(self, wallet_data):
        try:
            if wallet_data:
                self.player_wallet = wallet_data
                if self.verbose:
                    print(f"Updated player wallet: {self.player_wallet}")
        except Exception as e:
            logging.error(f"Unexpected error in update_player_wallet: {e}")

    def dispatch_summary(self):
        """
        Summarizes and dispatches the collected messages to the LLM agent at regular intervals.
        """
        print("Dispatch summary started.")

        if not self.message_queue.empty():
            print(f"Queue size before dispatch: {self.message_queue.qsize()}")

            messages_to_summarize = []

            while not self.message_queue.empty():
                item = self.message_queue.get()
                if isinstance(item, tuple) and len(item) == 2:
                    priority, message = item
                    messages_to_summarize.append(message)
                else:
                    logging.error(
                        f"Unexpected item structure in queue: {item}")
                    continue

            if messages_to_summarize:
                summary = self.summarize_messages(messages_to_summarize)
                # Include the current phase description in the summary
                phase_description = self.get_phase_description(
                    self.current_phase, self.user_role)
                summary += f"\nCurrent Phase ({self.current_phase}): {phase_description}\n"
                self.dispatch_summary_to_llm(summary)
            else:
                print("No valid messages to summarize.")
        else:
            print("No messages to summarize and dispatch.")
            if self.verbose:
                print("No messages to summarize and dispatch (verbose mode).")

        self.dispatch_timer = threading.Timer(self.dispatch_interval,
                                              self.dispatch_summary)
        self.dispatch_timer.start()

    def handle_phase_transition(self, phase_data):
        """
        Handles phase transitions and logs the phase description.
        """
        new_phase = phase_data.get('phase', self.current_phase)
        self.current_phase = new_phase

        # Get the description of the new phase
        phase_description = self.get_phase_description(new_phase,
                                                       self.user_role)

        if self.verbose:
            print(
                f"Phase Transitioned to Phase {new_phase}: {phase_description}")

        # You can also log this or add to the summary
        logging.info(
            f"Phase Transitioned to Phase {new_phase}: {phase_description}")

    def summarize_messages(self, messages):
        """
        Summarizes the collected messages into a single query.

        Args:
            messages (list): List of messages to be summarized.

        Returns:
            str: The summarized query string.
        """
        summary = "Simulation Events Summary:\n"

        # Track if the phase description has been added to avoid repetition
        phase_description_added = False

        for index, message in enumerate(messages):
            try:
                message_data = json.loads(message)
                message_type = message_data.get('type', None)
                event_type = message_data.get('eventType', None)

                if not phase_description_added:
                    # Include the phase description at the beginning of the summary, once per phase
                    phase_description = self.get_phase_description(
                        self.current_phase, self.user_role)
                    summary += f"Current Phase ({self.current_phase}): {phase_description}\n"
                    phase_description_added = True

                # Process other event types...
                if message_type == 'event':
                    # Handle events like assign-role, profit, etc.
                    pass
                elif message_type == 'info':
                    summary += f"Info: {message_data['message']}\n"
                elif message_type == 'notice':
                    summary += f"Notice: {message_data['message']}\n"

            except ValueError as ve:
                logging.error(f"ValueError in summarize_messages: {ve}")
            except KeyError as ke:
                logging.error(f"KeyError in summarize_messages: {ke}")
                logging.error(f"Message causing the error: {message}")
            except Exception as e:
                logging.error(
                    f"Error processing message {index + 1}/{len(messages)}: {e}")

        return summary

    def get_phase_description(self, phase_number, role):
        role_map = {1: "Speculator", 2: "Developer", 3: "Owner"}
        role_name = role_map.get(role, "Participant")

        phase_descriptions = {
            1: f"Presentation Phase: In this phase, you are presented with the current state of the game, including your role as {role_name}, your plots of land, and potential values of land under different conditions (Project or No Project). No direct interaction is required, but familiarize yourself with the information for upcoming decisions.",

            2: f"Declaration Phase: As an {role_name}, you need to declare the value of your plots of land for both potential outcomes: if the project is implemented or not. These declarations will determine the taxes you will pay and influence whether the Project or No Project condition is selected. Make sure your declarations are strategic to minimize taxes and optimize your position.",

            3: f"Speculation Phase: As a {role_name}, you can choose to buy plots of land based on the declared values from the previous phase. Assess the likelihood of profit by comparing declared values to the perceived real value of the land. If you decide not to buy, you can observe how the market plays out.",

            4: f"Reconciliation Phase: This phase calculates the profits and taxes based on the declarations and the chosen condition (Project or No Project). As an {role_name}, your taxes are calculated, and any snipes are processed. This phase provides a clear outcome of your earlier decisions.",

            5: f"Market Phase: As a {role_name}, participate in the market to trade tax shares. Evaluate the public and private signals to decide whether to buy or sell shares. The goal is to optimize your returns based on the perceived future tax income.",

            6: f"Final Declaration Phase: Submit your final declarations of the value of your property based on the chosen condition (Project or No Project). This declaration will be taxed at a higher rate (33%), so be strategic in setting your values.",

            7: f"Final Speculation Phase: Similar to the first speculation phase, but this time, your final declared values are in play. Decide whether to buy plots of land based on the final values and consider the potential for profit or loss.",

            8: f"Results Phase: This phase summarizes the outcomes of the round. You can see your earnings and how well you performed compared to others. Use this information to adjust your strategy for the next round."
        }

        return phase_descriptions.get(phase_number, "Unknown Phase")

    def dispatch_summary_to_llm(self, summary):
        """
        Dispatches the summary to the LLM communicator and handles the response.
        """
        print(f"Summary: \n {summary}")
        ws_message = self.llm_communicator.query_openai(summary)
        if ws_message:
            self.llm_communicator.send_to_websocket_client(self.websocket_client, ws_message)

    def stop_dispatcher(self):
        """
        Stops the dispatch timer gracefully.
        """
        self.dispatch_timer.cancel()


