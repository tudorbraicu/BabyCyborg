"""
DFA - Generic DFA engine for monitors and game components.

Monitors are communicating automata that evaluate actions via message passing.
"""
import yaml
import re
import logging
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class Monitor:
    """
    Communicating automaton monitor with two-step evaluation.

    Step 1: Receive action (?receive) and transition to new state
    Step 2: Emit success/failure (!emit) based on new state
    """

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.initial_state = config.get('initial_state', 'm0')
        self.states = config.get('states', [])
        self.transitions = config.get('transitions', [])
        self.current_state = self.initial_state
        self._validate_config()

    def _validate_config(self):
        """Validate monitor configuration."""
        if self.initial_state not in self.states:
            raise ValueError(
                f"Monitor '{self.name}': initial_state '{self.initial_state}' "
                f"not in states list"
            )

        for i, transition in enumerate(self.transitions):
            if 'from_state' not in transition:
                raise ValueError(f"Monitor '{self.name}': transition {i} missing 'from_state'")
            if 'to_state' not in transition:
                raise ValueError(f"Monitor '{self.name}': transition {i} missing 'to_state'")

    def reset(self):
        """Reset monitor to initial state."""
        self.current_state = self.initial_state

    def receive_action(self, agent: str, action: str, host_id: int) -> bool:
        """
        Step 1: Receive action and transition to new state.

        Args:
            agent: Agent name (e.g., 'Red', 'Blue')
            action: Action name (e.g., 'Impact', 'Remove')
            host_id: Host identifier (e.g., 0, 1, 2)

        Returns:
            bool: True if transition found, False if staying in current state
        """
        input_symbol = f"?{agent}_{action}_{host_id}"

        for transition in self.transitions:
            if transition['from_state'] == self.current_state:
                pattern = transition.get('transition', '')
                if pattern.startswith('?') and self._matches_pattern(input_symbol, pattern):
                    self.current_state = transition['to_state']
                    return True

        return False

    def emit_result(self) -> Tuple[bool, str]:
        """
        Step 2: Emit success/failure from current state.

        Returns:
            Tuple of (success: bool, emit_symbol: str)
        """
        for transition in self.transitions:
            if transition['from_state'] == self.current_state:
                emit_symbol = transition.get('transition', '')
                if emit_symbol.startswith('!'):
                    self.current_state = transition['to_state']

                    if emit_symbol == "!success":
                        return True, emit_symbol
                    elif emit_symbol == "!failure":
                        return False, emit_symbol
                    else:
                        logger.warning(f"Unknown emit symbol '{emit_symbol}' in monitor '{self.name}'")
                        return True, emit_symbol

        return True, "!success"

    def receive_ack(self, global_success: bool) -> bool:
        """
        Step 3: Receive ACK from referee about global action outcome.

        Args:
            global_success: True if action succeeded globally (1), False if blocked (0)

        Returns:
            bool: True if ACK transition found, False if no transition
        """
        ack_value = 1 if global_success else 0
        ack_symbol = f"?Referee_Result_{ack_value}"

        for transition in self.transitions:
            if transition['from_state'] == self.current_state:
                pattern = transition.get('transition', '')
                if pattern.startswith('?') and self._matches_pattern(ack_symbol, pattern):
                    self.current_state = transition['to_state']
                    return True

        return False

    def _matches_pattern(self, input_symbol: str, pattern: str) -> bool:
        """
        Check if input symbol matches pattern with wildcard support.

        Args:
            input_symbol: Input like "?Red_Impact_0"
            pattern: Pattern like "?Red_Impact_*" or "?Blue_*"

        Returns:
            bool: True if input matches pattern
        """
        regex_pattern = re.escape(pattern).replace(r'\*', '.*')
        regex_pattern = f"^{regex_pattern}$"
        return re.match(regex_pattern, input_symbol) is not None

    def get_state(self) -> str:
        """Get current state of the monitor."""
        return self.current_state

    def __repr__(self):
        return f"Monitor(name='{self.name}', state='{self.current_state}')"


class Referee:
    """
    Game referee that determines action success/failure using monitor automata.
    """

    def __init__(self, monitors_path: Optional[str] = None):
        self.monitors: List[Monitor] = []
        if monitors_path:
            self.load_monitors(monitors_path)

    def reset(self):
        """Reset all monitors."""
        for monitor in self.monitors:
            monitor.reset()

    def load_monitors(self, monitors_path: str):
        """Load monitors from a YAML file or directory."""
        self.monitors = load_monitors_from_yaml(monitors_path)

    def evaluate_via_monitors(self, agent: str, action: str, host_id: int) -> Tuple[bool, str]:
        """
        Evaluate action using communicating automata monitors with ACK protocol.

        Three-step process:
        1. Broadcast action to all monitors (receive phase)
        2. Collect emissions from all monitors (emit phase)
        3. Send ACK to all monitors with global outcome (synchronization phase)

        Args:
            agent: Agent performing the action
            action: Action being performed
            host_id: Target host ID

        Returns:
            Tuple of (success: bool, reason: str)
        """
        if not self.monitors:
            return True, "No monitors, default success"

        # Step 1: Broadcast action to all monitors
        for monitor in self.monitors:
            monitor.receive_action(agent, action, host_id)

        # Step 2: Collect emissions from all monitors
        global_success = True
        blocking_monitor = None

        for monitor in self.monitors:
            success, emit_symbol = monitor.emit_result()

            if not success:
                global_success = False
                if blocking_monitor is None:
                    blocking_monitor = monitor

        # Step 3: Send ACK to all monitors
        for monitor in self.monitors:
            monitor.receive_ack(global_success)

        # Return result
        if global_success:
            return True, "All monitors passed"
        else:
            return False, f"Monitor '{blocking_monitor.name}' blocked action"


def load_monitors_from_yaml(yaml_path: str) -> List[Monitor]:
    """
    Load monitors from a YAML file or directory.

    Args:
        yaml_path: Path to YAML file or directory containing monitor definitions

    Returns:
        List of Monitor instances
    """
    path = Path(yaml_path)
    if not path.exists():
        raise FileNotFoundError(f"Monitor file/directory not found: {yaml_path}")

    monitors = []

    if path.is_dir():
        yaml_files = sorted(path.glob('*.yaml'))
        for yaml_file in yaml_files:
            with open(yaml_file, 'r') as f:
                config = yaml.safe_load(f)

            # Single monitor per file
            if 'name' in config and 'initial_state' in config:
                name = config.get('name', yaml_file.stem)
                monitor = Monitor(name, config)
                monitors.append(monitor)
            # Multiple monitors per file
            elif 'monitors' in config:
                for monitor_config in config.get('monitors', []):
                    name = monitor_config.get('name', f'monitor_{len(monitors)}')
                    monitor = Monitor(name, monitor_config)
                    monitors.append(monitor)
    else:
        with open(yaml_path, 'r') as f:
            config = yaml.safe_load(f)

        for monitor_config in config.get('monitors', []):
            name = monitor_config.get('name', f'monitor_{len(monitors)}')
            monitor = Monitor(name, monitor_config)
            monitors.append(monitor)

    return monitors
