# GameHandlerFutarchy.py

import json
import threading
from queue import Queue
import logging
from LLMCommunicator import LLMCommunicator

# Configure Logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

class GameHandler:
    def __init__(self, game_id, websocket_client=None, verbose=False, recovery=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.game_id = game_id
        self.verbose = verbose
        self.recovery = recovery
        self.websocket_client = websocket_client

        # Game State
        self.current_phase = None
        self.current_round = 1
        self.user_number = None
        self.user_role = None
        self.player_wallet = {}
        self.properties = {}
        self.roles = {}
        self.in_market_phase = False

        # Message Queue
        self.message_queue = Queue(maxsize=100)
        self.dispatch_interval = 5  # seconds

        # Context Tracking
        self.context = {
            'player_actions': [],
            'declarations': [],
            'profits': [],
            'market_signals': [],
            'phase_transitions': []
        }

        # Maximum context sizes
        self.max_context = {
            'player_actions': 20,
            'declarations': 5,
            'profits': 10,
            'market_signals': 5,
            'phase_transitions': 10
        }

        # Relevant action types
        self.relevant_actions = [
            'declarations-published',
            'profit',
            'value-signals',
            'add-order',
            'contract-fulfilled',
            'delete-order',
            'phase-transition'
        ]

        # Initialize LLM Communicator
        self.llm_communicator = LLMCommunicator()

        # Dispatch Timer
        self.dispatch_timer = None

    def format_action(self, action_type, data):
        """
        Formats the action details based on the action type.
        """
        try:
            if action_type == 'declarations-published':
                decls = data.get('declarations', [])
                formatted_decls = "; ".join([
                    f"{decl['name']} by {decl['owner']} - Declarations: {decl['d']}"
                    for decl in decls
                ])
                return f"Declarations Published: {formatted_decls}"

            elif action_type == 'profit':
                return (
                    f"Profit: Round {data.get('round')}, Phase {data.get('phase')}, "
                    f"Property {data.get('property')}, Total = {data.get('total')}"
                )

            elif action_type == 'value-signals':
                return (
                    f"Market Signals: Signals={data.get('signals')}, "
                    f"PublicSignal={data.get('publicSignal')}, Tax Rate={data.get('taxRate')}"
                )

            elif action_type == 'add-order':
                order = data.get('order', {})
                return (
                    f"Add Order: ID={order.get('id')}, Sender={order.get('sender')}, "
                    f"Price={order.get('price')}, Type={order.get('type')}, "
                    f"Condition={order.get('condition')}"
                )

            elif action_type == 'contract-fulfilled':
                return (
                    f"Contract Fulfilled: From={data.get('from')}, To={data.get('to')}, "
                    f"Price={data.get('price')}, Condition={data.get('condition')}, Median={data.get('median')}"
                )

            elif action_type == 'delete-order':
                order = data.get('order', {})
                return (
                    f"Delete Order: ID={order.get('id')}, "
                    f"Type={order.get('type')}, Condition={order.get('condition')}"
                )

            else:
                return action_type.replace('-', ' ').capitalize()
        except Exception as e:
            self.logger.error(f"Error formatting action: {e}")
            return action_type.replace('-', ' ').capitalize()

    def add_to_context(self, category, item):
        """
        Adds an item to the specified context category, maintaining the maximum size.
        """
        if category not in self.context:
            self.logger.warning(f"Unknown context category: {category}")
            return

        if category == 'phase_transitions':
            # Simplify phase transitions
            flattened_item = {
                'phase': item.get('phase'),
                'round': item.get('round')
            }
            self.context[category].append(flattened_item)
        elif category == 'player_actions':
            self.context[category].append(item)
        else:
            self.context[category].append(item)

        # Maintain maximum context size
        if len(self.context[category]) > self.max_context.get(category, 10):
            removed_item = self.context[category].pop(0)
            self.logger.debug(f"Removed oldest item from {category}: {removed_item}")

    def receive_message(self, message):
        """
        Processes an incoming message from the WebSocket.
        """
        try:
            message_data = json.loads(message)
            event_type = message_data.get('eventType', '')
            message_type = message_data.get('type', '')

            self.logger.debug(f"Received message: {message_data}")

            # Queue the message for dispatching
            self.message_queue.put((2, message))

            # Add to context if relevant
            if event_type in self.relevant_actions:
                self.add_to_context('player_actions', {
                    'type': event_type,
                    'data': message_data.get('data', {})
                })

            # Handle specific event types
            if event_type == 'assign-name':
                self.handle_assign_name(message_data.get('data', {}))
            elif event_type == 'players-known':
                self.handle_players_known(message_data.get('data', {}).get('players', []))
            elif event_type == 'assign-role':
                self.handle_assign_role(message_data.get('data', {}))
            elif event_type == 'phase-transition':
                self.handle_phase_transition(message_data.get('data', {}))
            else:
                self.logger.debug(f"No specific handler for event type: {event_type}")

        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decoding error: {e} - Message: {message}")
        except Exception as e:
            self.logger.error(f"Unexpected error in receive_message: {e}")

    def handle_assign_name(self, data):
        """
        Handles the 'assign-name' event.
        """
        try:
            name = data['name']
            number = data['number']
            self.user_number = number
            self.logger.info(f"User assigned name: {name}, number: {number}")

            # Send 'player-is-ready' message
            self.send_player_ready()
        except KeyError as e:
            self.logger.error(f"Missing key in handle_assign_name: {e}")
        except Exception as e:
            self.logger.error(f"Error in handle_assign_name: {e}")

    def handle_players_known(self, players):
        """
        Handles the 'players-known' event dynamically, mapping player numbers to roles based on the message.

        Example message:
        {"type":"event","eventType":"players-known","data":{"players":[{"number":1,"role":3,"tag":"Owner 1"},
        {"number":2,"role":2,"tag":"Developer"},{"number":3,"role":1,"tag":"Speculator 1"}]}}

        This method dynamically maps roles to players based on the 'tag' field.
        """
        for player in players:
            number = player.get('number')
            role_name = player.get('tag', "Unknown")
            self.roles[number] = role_name

            if number == self.user_number:
                self.user_role = role_name

        self.logger.info(f"Player roles known: {self.roles}")
        if self.verbose:
            print(f"Player roles known: {self.roles}")

    def handle_assign_role(self, data):
        """
        Handles the 'assign-role' event.
        """
        try:
            role_number = data['role']
            role_map = {1: "Speculator", 2: "Developer", 3: "Owner"}
            self.user_role = role_map.get(role_number, "Unknown")
            self.logger.info(f"User assigned role: {self.user_role}")

            self.update_player_wallet(data.get('wallet', []))
            self.properties[self.user_number] = data.get('property', {})

            if self.verbose:
                print(f"User assigned role: {self.user_role}")
        except KeyError as e:
            self.logger.error(f"Missing key in handle_assign_role: {e}")
        except Exception as e:
            self.logger.error(f"Error in handle_assign_role: {e}")

    def update_player_wallet(self, wallet_data):
        """
        Updates the player's wallet based on provided data.
        """
        try:
            if wallet_data:
                total_balance = sum(wallet.get('balance', 0) for wallet in wallet_data)
                self.player_wallet['total_balance'] = total_balance
                self.logger.info(f"Updated player wallet: {self.player_wallet}")

                if self.verbose:
                    print(f"Updated player wallet: {self.player_wallet}")
        except Exception as e:
            self.logger.error(f"Error updating player wallet: {e}")

    def handle_phase_transition(self, phase_data):
        """
        Handles the 'phase-transition' event.
        """
        try:
            new_phase = int(phase_data.get('phase', self.current_phase))
            self.current_phase = new_phase
            self.logger.debug(f"New phase received: {new_phase} (Type: {type(new_phase)})")

            phase_description = self.get_phase_description(new_phase)
            if phase_description == "Unknown Phase":
                self.handle_unknown_phase(new_phase)

            self.logger.info(f"Phase Transitioned to Phase {new_phase}: {phase_description}")
            if self.verbose:
                print(f"Phase Transitioned to Phase {new_phase}: {phase_description}")

            # Add to context
            if 'phase-transition' in self.relevant_actions:
                self.add_to_context('phase_transitions', phase_data)

            # If new phase is 0, send 'player-is-ready' and handle accordingly
            if new_phase == 0:
                self.reset_context()
                self.send_player_ready()
                # Print the required message without dispatching the full summary
                ready_message = (
                    f"Phase Transitioned to Phase {new_phase}: {phase_description}\n\n"
                    f"Expected JSON Output:\n{{\n    \"gameId\": {self.game_id},\n    \"type\": \"player-is-ready\"\n}}"
                )
                print(ready_message)
                self.logger.debug("Game context has been reset.")
                print("Game context has been reset.")
                # Print phase dispatch started message
                dispatch_message = f"Phase {new_phase} dispatch started for role {self.user_role}."
                print(dispatch_message)
                self.logger.info(dispatch_message)
                # Do not call dispatch_summary()
                return

            # Dispatch summary for other phases
            self.dispatch_summary()

        except ValueError as e:
            self.logger.error(f"Invalid phase value: {phase_data.get('phase')} - {e}")
        except Exception as e:
            self.logger.error(f"Error handling phase transition: {e}")

    def handle_unknown_phase(self, phase_number):
        """
        Handles unknown phases.
        """
        self.logger.warning(f"Encountered unknown phase: {phase_number}")
        # Implement any additional logic for unknown phases if necessary

    def reset_context(self):
        """
        Resets the game context.
        """
        self.context = {
            'player_actions': [],
            'declarations': [],
            'profits': [],
            'market_signals': [],
            'phase_transitions': []
        }
        self.logger.debug("Game context has been reset.")
        if self.verbose:
            print("Game context has been reset.")

    def send_player_ready(self):
        """
        Sends the 'player-is-ready' message to the server.
        """
        try:
            is_ready_message = json.dumps({
                "gameId": self.game_id,
                "type": "player-is-ready"
            })
            if self.websocket_client:
                self.websocket_client.send_message(is_ready_message)
                self.logger.info(f"Sent 'player-is-ready' message: {is_ready_message}")
                if self.verbose:
                    print(f"Sent 'player-is-ready' message: {is_ready_message}")
            else:
                self.logger.error("WebSocket client is not available to send 'player-is-ready'.")
        except Exception as e:
            self.logger.error(f"Error sending 'player-is-ready' message: {e}")

    def dispatch_summary(self):
        """
        Dispatches a summary of events to the LLM for processing.
        """
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
            self.logger.debug(
                f"Phase {self.current_phase} dispatch started for role {self.user_role}."
            )
            print(f"Phase {self.current_phase} dispatch started for role {self.user_role}.")

            messages_to_summarize = []
            while not self.message_queue.empty():
                item = self.message_queue.get()
                if isinstance(item, tuple) and len(item) == 2:
                    priority, message = item
                    messages_to_summarize.append(message)
                else:
                    self.logger.error(f"Unexpected item structure in queue: {item}")

            summary = self.summarize_messages(messages_to_summarize)
            self.dispatch_summary_to_llm(summary)

            # If in phase 6, set up periodic dispatching
            if self.current_phase == 6:
                if self.dispatch_timer and self.dispatch_timer.is_alive():
                    self.dispatch_timer.cancel()
                self.dispatch_timer = threading.Timer(self.dispatch_interval, self.dispatch_summary)
                self.dispatch_timer.start()
                self.logger.debug("Dispatch timer set for periodic summary.")
        else:
            self.logger.info(
                f"No action required for Phase {self.current_phase} for role {self.user_role}."
            )
            print(f"No action required for Phase {self.current_phase} for role {self.user_role}.")

    def summarize_messages(self, messages):
        """
        Creates a summary of the received messages.
        """
        summary = "Simulation Events Summary:\n"

        phase_description = self.get_phase_description(self.current_phase)
        summary += f"Current Phase ({self.current_phase}): {phase_description}\n"

        if messages:
            for index, message in enumerate(messages):
                try:
                    message_data = json.loads(message)
                    message_type = message_data.get('type')
                    event_type = message_data.get('eventType')

                    if message_type == 'event' and event_type in self.relevant_actions:
                        self.process_event_for_summary(event_type, message_data.get('data', {}))
                    elif message_type in ['info', 'notice']:
                        summary += f"{message_type.capitalize()}: {message_data.get('message')}\n"
                except json.JSONDecodeError as ve:
                    self.logger.error(f"JSON decoding error in summarize_messages: {ve}")
                except KeyError as ke:
                    self.logger.error(f"Missing key in summarize_messages: {ke}")
                except Exception as e:
                    self.logger.error(f"Error processing message {index + 1}: {e}")

        else:
            summary += "No new messages received.\n"

        # Append cumulative context
        summary += "\nCumulative Context:\n"
        summary += self.build_cumulative_context()

        self.logger.debug(f"Summary created: {summary}")
        print(f"Summary: {summary}")
        return summary

    def process_event_for_summary(self, event_type, data):
        """
        Processes individual events to update context for the summary.
        """
        if event_type == 'profit':
            profit = {
                'round': data.get('round'),
                'phase': data.get('phase'),
                'property': data.get('property'),
                'value': data.get('value'),
                'taxes': data.get('taxes'),
                'total': data.get('total')
            }
            self.context['profits'].append(profit)

        elif event_type == 'declarations-published':
            declarations = [
                {
                    'id': decl.get('id'),
                    'name': decl.get('name'),
                    'owner': decl.get('owner'),
                    'd': decl.get('d'),
                    'available': decl.get('available')
                } for decl in data.get('declarations', [])
            ]
            self.context['declarations'].extend(declarations)

        elif event_type == 'value-signals':
            signals = {
                'signals': data.get('signals'),
                'publicSignal': data.get('publicSignal'),
                'condition': data.get('condition'),
                'taxRate': data.get('taxRate')
            }
            self.context['market_signals'].append(signals)

        elif event_type in ['add-order', 'contract-fulfilled', 'delete-order']:
            self.context['player_actions'].append({
                'type': event_type,
                'data': data
            })

    def build_cumulative_context(self):
        """
        Builds a string representing the cumulative context.
        """
        context_str = ""

        # Past Phase Transitions
        if self.context['phase_transitions']:
            context_str += f"Past Phase Transitions (last {self.max_context['phase_transitions']}): "
            phases = [f"Phase {pt['phase']} (Round {pt.get('round', 'N/A')})" for pt in self.context['phase_transitions']]
            context_str += ", ".join(phases) + "\n"

        # Recent Player Actions
        if self.context['player_actions']:
            context_str += f"Recent Player Actions (last {self.max_context['player_actions']}):\n"
            for action in self.context['player_actions']:
                formatted_action = self.format_action(action['type'], action.get('data', {}))
                context_str += f"- {formatted_action}\n"

        # Recent Declarations
        if self.context['declarations']:
            context_str += f"Recent Declarations (last {self.max_context['declarations']}):\n"
            for decl in self.context['declarations'][-self.max_context['declarations']:]:
                context_str += f"  * {decl['name']} by {decl['owner']} - Declarations: {decl['d']}\n"

        # Recent Profits
        if self.context['profits']:
            context_str += f"Recent Profits (last {self.max_context['profits']}):\n"
            for profit in self.context['profits'][-self.max_context['profits']:]:
                context_str += f"  * Round {profit['round']}, Phase {profit['phase']}: Total = {profit['total']}\n"

        # Recent Market Signals
        if self.context['market_signals']:
            context_str += f"Recent Market Signals (last {self.max_context['market_signals']}):\n"
            for signal in self.context['market_signals'][-self.max_context['market_signals']:]:
                context_str += f"  * Signals: {signal['signals']}, Tax Rate: {signal['taxRate']}\n"

        # Player Status
        context_str += "\nPlayer Status:\n"
        total_balance = self.player_wallet.get('total_balance', 0)
        context_str += f"Total Wallet Balance: {total_balance}\n"

        props = self.properties.get(self.user_number, {})
        context_str += f"Properties Owned: {props.get('name', 'None')}\n"

        if self.context['market_signals']:
            latest_signal = self.context['market_signals'][-1]
            context_str += (
                f"Latest Market Signal: Signals={latest_signal['signals']}, "
                f"Tax Rate={latest_signal['taxRate']}\n"
            )

        if self.context['profits']:
            recent_profit = self.context['profits'][-1]
            context_str += f"Recent Profits: Total={recent_profit['total']}\n"

        return context_str

    def get_phase_description(self, phase_number):
        """
        Returns a description for the given phase number with clear JSON format expectations.
        """
        phase_descriptions = {
            0: (
                "Player is Ready: The game waits until all players declare themselves ready. No action is required.\n\n"
                f"Expected JSON Output:\n{{\n    \"gameId\": {self.game_id},\n    \"type\": \"player-is-ready\"\n}}"
            ),
            1: "Presentation Phase: Players are shown private and public data. This is a passive phase with no actions required.",
            2: (
                "Declaration Phase: Owners and Developer should declare their expected revenue for the round.\n\n"
                "The 'declaration' array should contain three values:\n"
                "- Value for the status quo condition (no project)\n"
                "- Value for the project development\n"
                "- Optional third value, set to 0 (for future use)\n\n"
                f"Expected JSON Output:\n{{\n    \"gameId\": {self.game_id},\n    \"type\": \"declare\",\n    \"declaration\": [\n        value_for_no_project,  # Integer, expected revenue for no project\n        value_for_project,    # Integer, expected revenue for project development\n        0                     # Integer, always set to 0\n    ]\n}}"
            ),
            3: (
                "Speculation Phase: Speculators may challenge declarations by Owners and Developers.\n\n"
                "The 'snipe' array should contain two arrays:\n"
                "- First array lists owners to challenge for the status quo condition\n"
                "- Second array lists owners to challenge for the project development condition\n\n"
                f"Expected JSON Output:\n{{\n    \"gameId\": {self.game_id},\n    \"type\": \"done-speculating\",\n    \"snipe\": [\n        [owners_to_challenge_no_project],  # List of integers (player numbers)\n        [owners_to_challenge_project]     # List of integers (player numbers)\n    ]\n}}"
            ),
            4: "Waiting Phase: Players wait in this phase. No specific actions required.",
            5: "Waiting Phase: Players wait in this phase. No specific actions required.",
            6: (
                "Market Phase: Players now see their private signals and the public signals. Use these signals to decide your next trading move.\n\n"
                "The signals represent market data, and you should interpret them to determine whether you wish to post a buy (bid) or sell (ask) order.\n\n"
                "Market Signals:\n"
                "- 'signals': Your private signals, visible only to you\n"
                "- 'publicSignal': Signals visible to all players\n"
                "Use this data to inform your decision. You are responsible for setting the prices based on these signals.\n\n"
                f"Expected JSON Output (Post Order):\n{{\n    \"gameId\": {self.game_id},\n    \"type\": \"post-order\",\n    \"order\": {{\n        \"price\": your_chosen_price,   # Integer, price you decide based on signals\n        \"quantity\": 1,                # Integer, always 1\n        \"condition\": condition_number,  # Integer, 0 for status quo, 1 for project\n        \"type\": \"ask\" or \"bid\",    # String, 'ask' to sell, 'bid' to buy\n        \"now\": true_or_false          # Boolean, true for immediate execution\n    }}\n}}"
            ),
            7: (
                "Final Declaration Phase: Owners and Developers submit their final declaration for the winning condition.\n\n"
                f"Expected JSON Output:\n{{\n    \"gameId\": {self.game_id},\n    \"type\": \"declare\",\n    \"declaration\": [\n        final_value_for_winning_condition  # Integer, expected revenue for the winning condition\n    ]\n}}"
            ),
            8: (
                "Final Speculation Phase: Speculators can challenge the final declarations.\n\n"
                "The 'snipe' array works similarly to Phase 3, where speculators list owners to challenge.\n\n"
                f"Expected JSON Output:\n{{\n    \"gameId\": {self.game_id},\n    \"type\": \"done-speculating\",\n    \"snipe\": [\n        [owners_to_challenge]  # List of integers (player numbers)\n    ]\n}}"
            ),
            9: "Results Phase: Players are shown their results, and the next round begins shortly."
        }

        return phase_descriptions.get(phase_number, "Unknown Phase")

    def dispatch_summary_to_llm(self, summary):
        """
        Sends the summary to the LLM and dispatches the response.
        """
        try:
            ws_message = self.llm_communicator.query_openai(summary)

            if ws_message:
                self.llm_communicator.send_to_websocket_client(self.websocket_client, ws_message)
                self.logger.info(f"Dispatched summary to LLM and sent response: {ws_message}")
            else:
                self.logger.error("LLM did not return a valid response.")
        except Exception as e:
            self.logger.error(f"Error dispatching summary to LLM: {e}")

    def stop_dispatcher(self):
        """
        Stops the dispatch timer if it's running.
        """
        if self.dispatch_timer and self.dispatch_timer.is_alive():
            self.dispatch_timer.cancel()
            self.logger.debug("Dispatch timer stopped.")