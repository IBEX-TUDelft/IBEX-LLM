import json
import threading
from queue import Queue
import logging
import pandas as pd
from LLMCommunicator import LLMCommunicator

class GameHandler:
    def __init__(self, game_id, websocket_client=None, verbose=False, recovery=None, logger=None):
        self.logger = logger or logging.getLogger(f"GameHandler-{game_id}")
        self.game_id = game_id
        self.verbose = verbose
        self.recovery = recovery
        self.websocket_client = websocket_client

        self.current_phase = None
        self.current_round = 1
        self.user_number = None
        self.user_role = None
        self.player_wallet = {}
        self.properties = {}
        self.roles = {}
        self.in_market_phase = False

        self.message_queue = Queue(maxsize=50)
        self.dispatch_interval = 5

        self.context = {
            'player_actions': [],
            'declarations': [],
            'profits': [],
            'market_signals': [],
            'phase_transitions': [],
            'asset_movements': []
        }

        self.max_context = {
            'player_actions': 20,
            'declarations': 5,
            'profits': 10,
            'market_signals': 5,
            'phase_transitions': 10,
            'asset_movements': 10
        }

        self.relevant_actions = [
            'declarations-published',
            'profit',
            'value-signals',
            'add-order',
            'contract-fulfilled',
            'delete-order',
            'phase-transition',
            'order-refused',
            'asset-movement'
        ]

        self.llm_communicator = None

        self.dispatch_timer = None

        # Load metadata
        self.load_metadata()

    def load_metadata(self):
        """Load metadata from Excel files."""
        try:
            self.role_descriptions = pd.read_excel("./prompts/role_descriptions.xlsx").set_index("Role").to_dict()["Description"]
            self.role_phase_instructions = pd.read_excel("./prompts/role_phase_instructions.xlsx").set_index(["Phase", "Role"]).to_dict("index")
            self.game_metadata = pd.read_excel("./prompts/game_metadata.xlsx").set_index("Key").to_dict()["Value"]
            self.phase_descriptions = pd.read_excel("./prompts/phase_descriptions.xlsx").set_index("Phase").to_dict()["Description"]
            self.logger.info("Metadata successfully loaded.")
        except Exception as e:
            self.logger.error(f"Error loading metadata: {e}")

    def get_phase_description(self, phase_number):
        """Retrieve the description for a given phase."""
        return self.phase_descriptions.get(phase_number, "Unknown Phase")

    def get_role_instruction(self, phase, role):
        """Retrieve instructions for a specific role in a given phase."""
        key = (phase, role)
        instruction_data = self.role_phase_instructions.get(key, {})
        return instruction_data.get("Instruction", "No specific instructions.")

    def initialize_player(self, role):
        """Provide a description of the player's role."""
        return self.role_descriptions.get(role, "Unknown role.")

    def validate_game_parameters(self):
        """Ensure game parameters adhere to metadata constraints."""
        total_rounds = int(self.game_metadata.get("Total Rounds", 10))
        total_phases = int(self.game_metadata.get("Total Phases", 10))
        if self.current_round > total_rounds or self.current_phase > total_phases:
            self.logger.error("Invalid game parameters: Exceeding defined rounds or phases.")

    def dispatch_summary(self):
        """Generate a summary of messages and instructions for the current phase."""
        roles_requiring_action = self.get_roles_requiring_action(self.current_phase)

        base_user_role = self.user_role.split()[0]

        if base_user_role in roles_requiring_action:
            self.logger.debug(
                f"Phase {self.current_phase} dispatch started for role {self.user_role}."
            )

            summary = self.summarize_messages()

            instructions = self.get_role_instruction(self.current_phase, base_user_role)
            summary += f"\n\nRole-Specific Instructions:\n{instructions}"

            self.dispatch_summary_to_llm(summary)

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

    def get_roles_requiring_action(self, phase):
        """Retrieve roles requiring action for the current phase from metadata."""
        roles = []
        for (phase_key, role), data in self.role_phase_instructions.items():
            if phase_key == phase and data.get("Instruction"):
                roles.append(role)
        return roles

    def summarize_messages(self):
        """Summarize relevant messages and context."""
        summary = "Simulation Events Summary:\n"

        phase_description = self.get_phase_description(self.current_phase)
        summary += f"Current Phase ({self.current_phase}): {phase_description}\n"

        while not self.message_queue.empty():
            priority, message = self.message_queue.get()
            summary += f"- {message}\n"

        summary += "\nCumulative Context:\n"
        for category, items in self.context.items():
            summary += f"{category.capitalize()}: {items}\n"

        return summary

    def dispatch_summary_to_llm(self, summary):
        """Send the summary to the LLM and handle the response."""
        try:
            response = self.llm_communicator.query_openai(summary)
            if response:
                self.logger.info(f"Dispatched summary to LLM: {response}")
            else:
                self.logger.error("LLM did not return a valid response.")
        except Exception as e:
            self.logger.error(f"Error dispatching summary to LLM: {e}")

    def receive_message(self, message):
        """Process incoming messages and update context."""
        try:
            message_data = json.loads(message)
            event_type = message_data.get('eventType', '')

            if event_type in self.relevant_actions:
                self.add_to_context('player_actions', message_data)

            if event_type == 'phase-transition':
                self.handle_phase_transition(message_data.get('data', {}))

            self.message_queue.put((2, message))
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decoding error: {e} - Message: {message}")

    def add_to_context(self, category, item):
        """Add an item to the specified context category, ensuring size limits."""
        if category not in self.context:
            self.logger.warning(f"Unknown context category: {category}")
            return

        self.context[category].append(item)

        if len(self.context[category]) > self.max_context.get(category, 10):
            removed_item = self.context[category].pop(0)
            self.logger.debug(f"Removed oldest item from {category}: {removed_item}")

    def handle_phase_transition(self, phase_data):
        """Handle phase transitions and reset context if needed."""
        try:
            new_phase = int(phase_data.get('phase', self.current_phase))
            self.current_phase = new_phase
            self.logger.info(f"Phase Transitioned to Phase {new_phase}")

            if new_phase == 0:
                self.reset_context()

        except ValueError as e:
            self.logger.error(f"Invalid phase value: {e}")

    def reset_context(self):
        """Reset the game context for a new phase."""
        self.context = {
            'player_actions': [],
            'declarations': [],
            'profits': [],
            'market_signals': [],
            'phase_transitions': [],
            'asset_movements': []
        }
        self.logger.debug("Game context has been reset.")
