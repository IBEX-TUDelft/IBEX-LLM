import json
import threading
from queue import Queue
import logging
from LLMCommunicator import LLMCommunicator


class GameHandler:
    def __init__(self, game_id, websocket_client=None, verbose=False, recovery=None):
        self.game_id = game_id
        self.verbose = verbose
        self.recovery = recovery
        self.message_queue = Queue(maxsize=100)
        self.dispatch_interval = 5
        self.player_wallet = {}
        self.user_number = None
        self.user_role = None
        self.current_phase = None
        self.current_round = 1
        self.websocket_client = websocket_client
        self.roles = {}
        self.properties = {}
        self.in_market_phase = False

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
            message_type = message_data.get('type', '')

            self.message_queue.put((2, message))

            if event_type == 'assign-name':
                print(f"User assigned name: {message_data['data']['name']}")
                self.user_number = message_data['data']['number']
                is_ready_message = json.dumps({
                    "gameId": self.game_id,
                    "type": "player-is-ready"
                })
                if self.websocket_client:
                    self.websocket_client.send_message(is_ready_message)
                if self.verbose:
                    print(f"Sent 'player-is-ready' message: {is_ready_message}")
            elif event_type == 'players-known':
                self.handle_players_known(message_data['data']['players'])
            elif event_type == 'assign-role':
                self.handle_assign_role(message_data['data'])
            elif event_type == 'phase-transition':
                self.handle_phase_transition(message_data['data'])
            else:
                pass

        except json.JSONDecodeError as e:
            logging.error(f"GameHandler: Failed to decode message JSON: {e}")
            self.handle_decoding_error(message)
        except Exception as e:
            logging.error(f"Unexpected error in receive_message: {e}")

    def handle_decoding_error(self, message):
        logging.info(f"Handling decoding error for message: {message}")

    def handle_players_known(self, players):
        role_map = {1: "Owner", 2: "Developer", 3: "Owner", 4: "Owner", 5: "Owner", 6: "Owner", 7: "Speculator", 8: "Speculator", 9: "Speculator", 10: "Speculator", 11: "Speculator", 12: "Speculator"}
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
            role_number = data['role']
            role_map = {1: "Speculator", 2: "Developer", 3: "Owner"}
            self.user_role = role_map.get(role_number, "Unknown")
            if self.verbose:
                print(f"User assigned role: {self.user_role}")

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
        new_phase = phase_data.get('phase', self.current_phase)
        self.current_phase = new_phase

        phase_description = self.get_phase_description(new_phase)
        if phase_description == "Unknown Phase":
            self.handle_unknown_phase(new_phase)

        if self.verbose:
            print(f"Phase Transitioned to Phase {new_phase}: {phase_description}")

        logging.info(f"Phase Transitioned to Phase {new_phase}: {phase_description}")

        self.dispatch_summary()

    def handle_unknown_phase(self, phase_number):
        logging.warning(f"Handling unknown phase: {phase_number}")
        self.dispatch_summary_to_llm(f"Unknown phase encountered: {phase_number}. Please review past actions and prepare accordingly.")

    def dispatch_summary(self):
        action_required_phases = {
            0: ["Owner", "Developer", "Speculator"],
            1: [],
            2: ["Owner", "Developer"],
            3: ["Speculator"],
            4: [],
            5: [],
            6: ["Owner", "Developer", "Speculator"],
            7: ["Owner", "Developer"],
            8: ["Speculator"],
            9: []
        }

        roles_requiring_action = action_required_phases.get(self.current_phase, [])

        if self.user_role in roles_requiring_action:
            print(f"Phase {self.current_phase} dispatch started for role {self.user_role}.")
            messages_to_summarize = []
            while not self.message_queue.empty():
                item = self.message_queue.get()
                if isinstance(item, tuple) and len(item) == 2:
                    priority, message = item
                    messages_to_summarize.append(message)
                else:
                    logging.error(f"Unexpected item structure in queue: {item}")
                    continue

            summary = self.summarize_messages(messages_to_summarize)
            self.dispatch_summary_to_llm(summary)

            if self.current_phase == 6:
                self.dispatch_timer = threading.Timer(self.dispatch_interval, self.dispatch_summary)
                self.dispatch_timer.start()
        else:
            print(f"No action required for Phase {self.current_phase} for role {self.user_role}.")

    def summarize_messages(self, messages):
        summary = "Simulation Events Summary:\n"

        phase_description = self.get_phase_description(self.current_phase, self.user_role)
        summary += f"Current Phase ({self.current_phase}): {phase_description}\n"

        if messages:
            for index, message in enumerate(messages):
                try:
                    message_data = json.loads(message)
                    message_type = message_data.get('type', None)
                    event_type = message_data.get('eventType', None)

                    if message_type == 'event':
                        if event_type == 'profit':
                            self.context['profits'].append(message_data['data'])
                        elif event_type == 'declarations-published':
                            self.context['declarations'].append(message_data['data']['declarations'])
                        elif event_type == 'value-signals':
                            self.context['market_signals'].append(message_data['data'])
                        self.context['player_actions'].append({'type': event_type, 'data': message_data['data']})

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
        else:
            summary += "No new messages received.\n"

        summary += "\nCumulative Context:\n"
        summary += f"Past Phase Transitions: {self.context['phase_transitions']}\n"
        summary += f"Player Actions: {self.context['player_actions']}\n"
        summary += f"Declarations: {self.context['declarations']}\n"
        summary += f"Profits: {self.context['profits']}\n"
        summary += f"Market Signals: {self.context['market_signals']}\n"

        return summary

    def get_phase_description(self, phase_number, role=None):
        role_name = role or self.user_role or "Participant"

        phase_descriptions = {
            0: "Player is Ready: The game waits until all players declare themselves ready. No action is required.\n\nExpected JSON Output:\n{\n    \"gameId\": %s,\n    \"type\": \"player-is-ready\"\n}" % self.game_id,
            1: "Presentation Phase: Players are shown private and public data. This is a passive phase.",
            2: "Declaration Phase: Owners and Developer should declare their expected revenue for the round.\n\nExpected JSON Output:\n{\n    \"gameId\": %s,\n    \"type\": \"declare\",\n    \"declaration\": [\n        value_for_no_project,\n        value_for_project,\n        0\n    ]\n}" % self.game_id,
            3: "Speculation Phase: Speculators may decide to challenge declarations by Owners and Developer.\n\nExpected JSON Output:\n{\n    \"gameId\": %s,\n    \"type\": \"done-speculating\",\n    \"snipe\": [\n        [owners_to_challenge_no_project],\n        [owners_to_challenge_project]\n    ]\n}" % self.game_id,
            4: "Waiting Phase: Players wait in this phase.",
            5: "Waiting Phase: Players wait in this phase.",
            6: "Market Phase: All players can post and cancel orders.\n\nExpected JSON Output (Post Order):\n{\n    \"gameId\": %s,\n    \"type\": \"post-order\",\n    \"order\": {\n        \"price\": price_value,\n        \"quantity\": 1,\n        \"condition\": condition_number,\n        \"type\": \"ask_or_bid\",\n        \"now\": true_or_false\n    }\n}" % self.game_id,
            7: "Final Declaration Phase: Owners and Developer submit their final declaration for the winning condition.\n\nExpected JSON Output:\n{\n    \"gameId\": %s,\n    \"type\": \"declare\",\n    \"declaration\": [\n        final_value_for_winning_condition\n    ]\n}" % self.game_id,
            8: "Final Speculation Phase: Speculators may speculate again.\n\nExpected JSON Output:\n{\n    \"gameId\": %s,\n    \"type\": \"done-speculating\",\n    \"snipe\": [\n        [owners_to_challenge]\n    ]\n}" % self.game_id,
            9: "Results Phase: Players are shown their results and wait for the next round."
        }

        return phase_descriptions.get(phase_number, "Unknown Phase")

    def dispatch_summary_to_llm(self, summary):
        ws_message = self.llm_communicator.query_openai(summary)

        if ws_message:
            self.llm_communicator.send_to_websocket_client(
                self.websocket_client, ws_message)

    def stop_dispatcher(self):
        if hasattr(self, 'dispatch_timer'):
            self.dispatch_timer.cancel()
