"""
StateManager - Handles host state management and transitions.

Separates state logic from the main simulator for better modularity.
"""
from typing import List, Dict, Any


class StateManager:
    """Manages host states and state transitions."""

    def __init__(self, scenario_config: Dict[str, Any]):
        """Initialize state manager with scenario configuration."""
        self.scenario_config = scenario_config
        self.num_hosts = scenario_config['Topology']['num_hosts']
        self.host_names = scenario_config['Topology']['hosts']
        self.initial_states = self._extract_initial_states()
        self._hosts: List[str] = []

    def _extract_initial_states(self) -> List[str]:
        """Extract initial states for each host from scenario."""
        hosts_config = self.scenario_config.get('Hosts', {})
        initial_states = []

        for host_name in self.host_names:
            host_config = hosts_config.get(host_name, {})
            initial_state = host_config.get('initial_state', 'q0')
            initial_states.append(initial_state)

        return initial_states

    def reset(self) -> List[str]:
        """Reset all hosts to their initial states."""
        self._hosts = self.initial_states.copy()
        return self._hosts.copy()

    def get_state_vector(self) -> List[str]:
        """Get current state of all hosts."""
        return self._hosts.copy()

    def get_host_state(self, host_id: int) -> str:
        """Get state of specific host."""
        if 0 <= host_id < len(self._hosts):
            return self._hosts[host_id]
        raise ValueError(f"Invalid host_id: {host_id}")

    def set_host_state(self, host_id: int, new_state: str) -> None:
        """Set state of specific host."""
        if 0 <= host_id < len(self._hosts):
            self._hosts[host_id] = new_state
        else:
            raise ValueError(f"Invalid host_id: {host_id}")

    def validate_state(self, state: str) -> bool:
        """Validate if a state is defined in the scenario."""
        valid_states = self.scenario_config.get('States', [])
        return state in valid_states

    def can_transition(self, from_state: str, to_state: str, action: str, agent: str) -> bool:
        """
        Check if a state transition is valid.

        This is where we'll add complex transition logic like:
        - Prerequisites checking
        - State dependencies
        - Conditional transitions
        - Resource requirements

        Args:
            from_state: Current state
            to_state: Target state
            action: Action being performed
            agent: Agent performing action

        Returns:
            True if transition is valid, False otherwise
        """
        # Basic validation for now
        if not self.validate_state(from_state) or not self.validate_state(to_state):
            return False

        # Get action definition from scenario
        agent_actions = self.scenario_config.get('Agents', {}).get(agent, {}).get('actions', {})
        action_def = agent_actions.get(action, {})

        if not action_def:
            return False  # Action not defined for this agent

        # Check from_state requirement
        required_from_state = action_def.get('from_state')
        if required_from_state != 'any' and required_from_state != from_state:
            return False

        # Validate to_state matches action definition
        expected_to_state = action_def.get('to_state')

        # Handle special cases
        if expected_to_state == 'same':
            return to_state == from_state
        elif expected_to_state == 'q1' and action == 'Remove':
            # Special Remove logic: q0->q0, others->q1
            expected = 'q0' if from_state == 'q0' else 'q1'
            return to_state == expected
        else:
            return to_state == expected_to_state