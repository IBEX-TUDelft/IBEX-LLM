import json
import threading
from queue import Queue
import logging
from LLMCommunicator import LLMCommunicator

class GameHandler:
    def __init__(self, game_id, websocket_client=None, verbose=False,
                 recovery=None):
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

        # Define maximum context sizes
        self.max_context = {
            'player_actions': 20,  # Keep last 20 actions
            'declarations': 5,  # Keep last 5 declarations
            'profits': 10,  # Keep last 10 profit records
            'market_signals': 5,  # Keep last 5 market signals
            'phase_transitions': 10  # Keep last 10 phase transitions
        }

        # Define relevant action types
        self.relevant_actions = [
            'declarations-published',
            'profit',
            'value-signals',
            'add-order',
            'contract-fulfilled',
            'delete-order'
        ]

    def format_action(self, action_type, data):
        """
        Formats the action details based on the action type.

        Args:
            action_type (str): The type of action.
            data (dict): The data associated with the action.

        Returns:
            str: A formatted string representing the action details.
        """
        if action_type == 'declarations-published':
            decls = data.get('declarations', [])
            formatted_decls = "; ".join([
                                            f"{decl['name']} by {decl['owner']} - Declarations: {decl['d']}"
                                            for decl in decls])
            return f"Declarations Published: {formatted_decls}"

        elif action_type == 'profit':
            return (
                f"Profit: Round {data.get('round')}, Phase {data.get('phase')}, "
                f"Property {data.get('property')}, Total = {data.get('total')}")

        elif action_type == 'value-signals':
            return (f"Market Signals: Signals={data.get('signals')}, "
                    f"PublicSignal={data.get('publicSignal')}, Tax Rate={data.get('taxRate')}")

        elif action_type == 'add-order':
            return (
                f"Add Order: ID={data.get('order', {}).get('id')}, Sender={data.get('order', {}).get('sender')}, "
                f"Price={data.get('order', {}).get('price')}, Type={data.get('order', {}).get('type')}, "
                f"Condition={data.get('order', {}).get('condition')}")

        elif action_type == 'contract-fulfilled':
            return (
                f"Contract Fulfilled: From={data.get('from')}, To={data.get('to')}, "
                f"Price={data.get('price')}, Condition={data.get('condition')}, Median={data.get('median')}")

        elif action_type == 'delete-order':
            return (f"Delete Order: ID={data.get('order', {}).get('id')}, "
                    f"Type={data.get('order', {}).get('type')}, Condition={data.get('order', {}).get('condition')}")

        else:
            # For other action types, return only the type with formatting
            return action_type.replace('-', ' ').capitalize()

    def add_to_context(self, category, item):
        if category in self.context:
            if category == 'phase_transitions':
                # Flatten the item to reduce verbosity
                flattened_item = {
                    'phase': item.get('phase'),
                    'round': item.get('round')
                }
                self.context[category].append(flattened_item)
            elif category == 'player_actions':
                # Already simplified elsewhere
                self.context[category].append(item)
            else:
                self.context[category].append(item)

            # Enforce max context size
            if len(self.context[category]) > self.max_context.get(category,
                                                                  10):
                self.context[category].pop(0)
        else:
            logging.warning(
                f"Attempted to add to unknown context category: {category}")

    def receive_message(self, message):
        try:
            message_data = json.loads(message)
            event_type = message_data.get('eventType', '')
            message_type = message_data.get('type', '')

            self.message_queue.put((2, message))

            # Add the message to the appropriate context if it's relevant
            if event_type and event_type in self.relevant_actions:
                self.add_to_context('player_actions', {'type': event_type,
                                                       'data': message_data.get(
                                                           'data', {})})

            # Handle specific event types
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
                    print(
                        f"Sent 'player-is-ready' message: {is_ready_message}")
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
        role_map = {1: "Owner", 2: "Developer", 3: "Speculator"}
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
                # Assuming wallet_data is a list of wallets, sum them up
                total_balance = sum(
                    wallet['balance'] for wallet in wallet_data)
                self.player_wallet['total_balance'] = total_balance
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
            print(
                f"Phase Transitioned to Phase {new_phase}: {phase_description}")

        logging.info(
            f"Phase Transitioned to Phase {new_phase}: {phase_description}")

        # Add to context only if it's a relevant action
        if 'phase-transition' in self.relevant_actions:
            self.add_to_context('phase_transitions', phase_data)

        # Reset contexts if transitioning to a new round
        if new_phase == 0:
            self.context = {
                'player_actions': [],
                'declarations': [],
                'profits': [],
                'market_signals': [],
                'phase_transitions': []
            }

        self.dispatch_summary()

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

        roles_requiring_action = action_required_phases.get(self.current_phase,
                                                            [])

        if self.user_role in roles_requiring_action:
            print(
                f"Phase {self.current_phase} dispatch started for role {self.user_role}.")
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

            summary = self.summarize_messages(messages_to_summarize)
            self.dispatch_summary_to_llm(summary)

            if self.current_phase == 6:
                self.dispatch_timer = threading.Timer(self.dispatch_interval,
                                                      self.dispatch_summary)
                self.dispatch_timer.start()
        else:
            print(
                f"No action required for Phase {self.current_phase} for role {self.user_role}.")

    def summarize_messages(self, messages):
        summary = "Simulation Events Summary:\n"

        phase_description = self.get_phase_description(self.current_phase,
                                                       self.user_role)
        summary += f"Current Phase ({self.current_phase}): {phase_description}\n"

        if messages:
            for index, message in enumerate(messages):
                try:
                    message_data = json.loads(message)
                    message_type = message_data.get('type', None)
                    event_type = message_data.get('eventType', None)

                    if message_type == 'event' and event_type in self.relevant_actions:
                        if event_type == 'profit':
                            profit = {
                                'round': message_data['data'].get('round'),
                                'phase': message_data['data'].get('phase'),
                                'property': message_data['data'].get(
                                    'property'),
                                'value': message_data['data'].get('value'),
                                'taxes': message_data['data'].get('taxes'),
                                'total': message_data['data'].get('total')
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
                                } for decl in
                                message_data['data']['declarations']
                            ]
                            self.context['declarations'].append(declarations)
                        elif event_type == 'value-signals':
                            signals = {
                                'signals': message_data['data'].get('signals'),
                                'publicSignal': message_data['data'].get(
                                    'publicSignal'),
                                'condition': message_data['data'].get(
                                    'condition'),
                                'taxRate': message_data['data'].get('taxRate')
                            }
                            self.context['market_signals'].append(signals)
                        elif event_type in ['add-order', 'contract-fulfilled',
                                            'delete-order']:
                            self.context['player_actions'].append(
                                {'type': event_type,
                                 'data': message_data.get('data', {})})

                    elif message_type in ['info', 'notice']:
                        summary += f"{message_type.capitalize()}: {message_data.get('message')}\n"

                except ValueError as ve:
                    logging.error(f"ValueError in summarize_messages: {ve}")
                except KeyError as ke:
                    logging.error(f"KeyError in summarize_messages: {ke}")
                    logging.error(f"Message causing the error: {message}")
                except Exception as e:
                    logging.error(
                        f"Error processing message {index + 1}/{len(messages)}: {e}")
        else:
            summary += "No new messages received.\n"

        # Add condensed cumulative context
        summary += "\nCumulative Context:\n"

        # Past Phase Transitions
        if self.context['phase_transitions']:
            summary += f"Past Phase Transitions (last {self.max_context['phase_transitions']}): "
            phases = [f"Phase {pt['phase']} (Round {pt.get('round', 'N/A')})"
                      for pt in self.context['phase_transitions']]
            summary += ", ".join(phases) + "\n"

        # Recent Player Actions with Details
        if self.context['player_actions']:
            summary += f"Recent Player Actions (last {self.max_context['player_actions']}):\n"
            for action in self.context['player_actions']:
                formatted_action = self.format_action(action['type'],
                                                      action.get('data', {}))
                summary += f"- {formatted_action}\n"

        # Recent Declarations
        if self.context['declarations']:
            summary += f"Recent Declarations (last {self.max_context['declarations']}):\n"
            for decl_list in self.context['declarations']:
                for decl in decl_list:
                    summary += f"  * {decl['name']} by {decl['owner']} - Declarations: {decl['d']}\n"

        # Recent Profits
        if self.context['profits']:
            summary += f"Recent Profits (last {self.max_context['profits']}):\n"
            for profit in self.context['profits']:
                summary += f"  * Round {profit['round']}, Phase {profit['phase']}: Total = {profit['total']}\n"

        # Recent Market Signals
        if self.context['market_signals']:
            summary += f"Recent Market Signals (last {self.max_context['market_signals']}):\n"
            for signal in self.context['market_signals']:
                summary += f"  * Signals: {signal['signals']}, Tax Rate: {signal['taxRate']}\n"

        # Add Player Status
        summary += "\nPlayer Status:\n"
        # Simplify wallet balance by summing or selecting relevant parts
        total_balance = self.player_wallet.get('total_balance', 0)
        summary += f"Total Wallet Balance: {total_balance}\n"
        # Simplify properties owned
        props = self.properties.get(self.user_number, {})
        summary += f"Properties Owned: {props.get('name', 'None')}\n"
        # Latest Market Signals
        if self.context['market_signals']:
            latest_signal = self.context['market_signals'][-1]
            summary += (
                f"Latest Market Signal: Signals={latest_signal['signals']}, "
                f"Tax Rate={latest_signal['taxRate']}\n")
        # Recent Profits
        if self.context['profits']:
            recent_profit = self.context['profits'][-1]
            summary += f"Recent Profits: Total={recent_profit['total']}\n"


        print(f"Summary: {summary}")
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
            6: (
                "Market Phase: All players can post and cancel orders. "
                "You may choose to post 'bid' orders to buy assets or 'ask' orders to sell assets you own. "
                "There are two conditions in this phase: Condition 0 and Condition 1. "
                "Condition 0 typically refers to the standard market operations, while Condition 1 may involve special rules or exceptions. "
                "Consider the current market conditions, your objectives, and potential profitability when deciding whether to bid or ask. "
                "If you wish to acquire assets, posting 'bid' orders might be advantageous. "
                "If you want to sell assets you own, consider posting 'ask' orders. "
                "Make your decision based on the events and context provided.\n\n"
                "Expected JSON Output (Post Order):\n"
                "{\n"
                "    \"gameId\": %s,\n"
                "    \"type\": \"post-order\",\n"
                "    \"order\": {\n"
                "        \"price\": price_value (within 1-9),\n"
                "        \"quantity\": 1,\n"
                "        \"condition\": condition_number,  # 0 or 1 as defined\n"
                "        \"type\": \"ask\" or \"bid\",  # Choose 'ask' or 'bid' based on your strategy\n"
                "        \"now\": true_or_false\n"
                "    }\n"
                "}" % self.game_id,
            ),
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
