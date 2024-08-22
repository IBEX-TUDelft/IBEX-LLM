import json
import threading
from queue import Queue
import logging
from src.LLMCommunicator import LLMCommunicator

class GameHandler:
    def __init__(self, game_id, websocket_client=None, verbose=False, recovery=None):
        self.game_id = game_id
        self.verbose = verbose
        self.recovery = recovery  # Store the recovery value
        self.message_queue = Queue(maxsize=10)
        self.dispatch_interval = 5  # Dispatch interval during the Market Phase
        self.player_wallet = {}
        self.user_number = None
        self.user_role = None
        self.current_phase = 1
        self.current_round = 1
        self.websocket_client = websocket_client
        self.roles = {}
        self.properties = {}
        self.in_market_phase = False  # Flag to check if the Market Phase is active

        # Start the dispatch timer
        self.dispatch_timer = threading.Timer(self.dispatch_interval, self.dispatch_summary)
        self.dispatch_timer.start()

        self.llm_communicator = LLMCommunicator()

        self.context = {
            'player_actions': [],
            'declarations': [],
            'profits': [],
            'market_signals': [],
            'phase_transitions': []
        }

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
                self.dispatch_summary()  # Send summary at the end of each phase
            else:
                self.message_queue.put((2, message))  # Default priority

            if self.verbose:
                print(f"Message received: {message}")

        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode message JSON: {e}")
            self.handle_decoding_error(message)
        except Exception as e:
            logging.error(f"Unexpected error in receive_message: {e}")

    def handle_decoding_error(self, message):
        # Simplified fallback strategy for handling decoding errors
        logging.info(f"Handling decoding error for message: {message}")
        # Implement additional fallback logic as needed

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

    def handle_phase_transition(self, phase_data):
        """
        Handles phase transitions and logs the phase description.
        """
        new_phase = phase_data.get('phase', self.current_phase)
        self.current_phase = new_phase

        # Send "is ready" message when Phase 0 occurs
        if new_phase == 0:
            is_ready_message = json.dumps({
                "gameId": self.game_id,
                "type": "join",
                "recovery": self.recovery
            })
            if self.websocket_client:
                self.websocket_client.send(is_ready_message)
            if self.verbose:
                print(f"Sent 'is ready' message: {is_ready_message}")

        # Track phase transitions for context
        self.context['phase_transitions'].append(new_phase)

        # Ensure the phase is correctly handled, especially for unknown phases
        phase_description = self.get_phase_description(new_phase,
                                                       self.user_role)
        if phase_description == "Unknown Phase":
            self.handle_unknown_phase(new_phase)

        # Update the market phase flag
        self.in_market_phase = (new_phase == 6)

        if self.verbose:
            print(
                f"Phase Transitioned to Phase {new_phase}: {phase_description}")

        logging.info(
            f"Phase Transitioned to Phase {new_phase}: {phase_description}")

    def handle_unknown_phase(self, phase_number):
        """
        Handle scenarios where the phase is unknown or not recognized.
        """
        logging.warning(f"Handling unknown phase: {phase_number}")
        self.dispatch_summary_to_llm(f"Unknown phase encountered: {phase_number}. Please review past actions and prepare accordingly.")

    def dispatch_summary(self):
        """
        Summarizes and dispatches the collected messages to the LLM agent.
        During the Market Phase, dispatches occur every X seconds or after X messages.
        """
        if self.current_phase == 6:  # Market Phase
            print("Market Phase dispatch started.")
            if not self.message_queue.empty():
                print(
                    f"Queue size before dispatch: {self.message_queue.qsize()}")

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
                    self.dispatch_summary_to_llm(summary)
                else:
                    print("No valid messages to summarize.")
            else:
                print("No messages to summarize and dispatch.")

            self.dispatch_timer = threading.Timer(self.dispatch_interval,
                                                  self.dispatch_summary)
            self.dispatch_timer.start()
        else:
            print("End-of-Phase dispatch started.")
            if not self.message_queue.empty():
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
                    self.dispatch_summary_to_llm(summary)
                else:
                    print("No valid messages to summarize.")
            else:
                print("No messages to summarize and dispatch.")

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
                    phase_description = self.get_phase_description(self.current_phase, self.user_role)
                    summary += f"Current Phase ({self.current_phase}): {phase_description}\n"
                    phase_description_added = True

                # Process events and store them in context
                if message_type == 'event':
                    if event_type == 'profit':
                        self.context['profits'].append(message_data['data'])
                    elif event_type == 'declarations-published':
                        self.context['declarations'].append(message_data['data']['declarations'])
                    elif event_type == 'value-signals':
                        self.context['market_signals'].append(message_data['data'])
                    # Track player actions
                    self.context['player_actions'].append({'type': event_type, 'data': message_data['data']})

                # Include event and info messages in the summary
                if message_type == 'event':
                    summary += f"Event: {event_type} with data {message_data['data']}\n"
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
                logging.error(f"Error processing message {index + 1}/{len(messages)}: {e}")

        # Add cumulative context summary
        summary += "\nCumulative Context:\n"
        summary += f"Past Phase Transitions: {self.context['phase_transitions']}\n"
        summary += f"Player Actions: {self.context['player_actions']}\n"
        summary += f"Declarations: {self.context['declarations']}\n"
        summary += f"Profits: {self.context['profits']}\n"
        summary += f"Market Signals: {self.context['market_signals']}\n"

        return summary

    def get_phase_description(self, phase_number, role):
        role_map = {1: "Speculator", 2: "Developer", 3: "Owner"}
        role_name = role_map.get(role, "Participant")

        phase_descriptions = {
            0: f"Introduction Phase: In this phase, players are introduced to the game and its rules. Familiarize yourself with the roles and objectives to prepare for the upcoming phases.",

            1: f"Presentation Phase: In this phase, you are presented with the current state of the game, including your role as {role_name}, your plots of land, and potential values of land under different conditions (Project or No Project). No direct interaction is required, but familiarize yourself with the information for upcoming decisions.",

            2: f"Declaration Phase: As an {role_name}, you need to declare the value of your plots of land for both potential outcomes: if the project is implemented or not. These declarations will influence the initial market signals and help determine which outcome will be favored. Ensure your declarations align with your market expectations.",

            3: f"Speculation Phase: As a {role_name}, you can choose to buy or sell shares in the markets based on the declared values from the previous phase. Assess the likelihood of each outcome (Project or No Project) being selected based on the market activity and adjust your strategy accordingly.",

            4: f"Market Phase: This is the critical phase where you trade shares in two parallel markets—one for each possible outcome (Project or No Project). The outcome with the highest median price at the end of the phase determines the project's fate. Trade wisely to influence and benefit from the final decision.",

            5: f"Reconciliation Phase: This phase calculates the profits and taxes based on the final market outcome and the final declarations. As an {role_name}, review the results to see how your market actions impacted your earnings.",

            6: f"Final Declaration Phase: Submit your final declarations of the value of your property based on the chosen condition (Project or No Project). This declaration will be taxed at a higher rate (33%), so be strategic in setting your values.",

            7: f"Final Speculation Phase: Similar to the earlier speculation phase, but this time, your final declared values are in play. Decide whether to buy or sell shares based on the final market conditions and consider the potential for profit or loss.",

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
