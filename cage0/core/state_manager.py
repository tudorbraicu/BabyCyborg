"""
StateManager - Handles host state management and transitions.

Separates state logic from the main simulator for better modularity.
"""
from typing import List, Dict, Any


class StateManager:
    """Manages host states and agent states with state transitions."""

    def __init__(self, scenario_config: Dict[str, Any]):
        """Initialize state manager with scenario configuration."""
        self.scenario_config = scenario_config
        self.num_hosts = scenario_config['Topology']['num_hosts']
        self.host_names = scenario_config['Topology']['hosts']
        self.initial_states = self._extract_initial_states()
        self._hosts: List[str] = []

        # Agent state management
        self.agent_names = list(scenario_config.get('Agents', {}).keys())
        self.agent_initial_states = self._extract_agent_initial_states()
        self._agents: Dict[str, str] = {}

    def _extract_initial_states(self) -> List[str]:
        """Extract initial states for each host from scenario."""
        hosts_config = self.scenario_config.get('Hosts', {})
        initial_states = []

        for host_name in self.host_names:
            host_config = hosts_config.get(host_name, {})
            initial_state = host_config.get('initial_state', 'q0')
            initial_states.append(initial_state)

        return initial_states

    def _extract_agent_initial_states(self) -> Dict[str, str]:
        """Extract initial states for each agent from scenario."""
        agents_config = self.scenario_config.get('Agents', {})
        agent_initial_states = {}

        for agent_name, agent_config in agents_config.items():
            initial_state = agent_config.get('initial_state', 'p0')
            agent_initial_states[agent_name] = initial_state

        return agent_initial_states

    def reset(self) -> List[str]:
        """Reset all hosts and agents to their initial states."""
        self._hosts = self.initial_states.copy()
        self._agents = self.agent_initial_states.copy()
        return self.get_state_vector()

    def get_state_vector(self) -> List[str]:
        """Get current state vector: [host_states..., agent_states...]."""
        state_vector = self._hosts.copy()
        # Append agent states in consistent order
        for agent_name in self.agent_names:
            state_vector.append(self._agents.get(agent_name, 'p0'))
        return state_vector

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

    def get_agent_state(self, agent_name: str) -> str:
        """Get state of specific agent."""
        if agent_name in self._agents:
            return self._agents[agent_name]
        raise ValueError(f"Invalid agent_name: {agent_name}")

    def set_agent_state(self, agent_name: str, new_state: str) -> None:
        """Set state of specific agent."""
        if agent_name in self.agent_names:
            self._agents[agent_name] = new_state
        else:
            raise ValueError(f"Invalid agent_name: {agent_name}")

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

        # Handle different to_state formats
        if expected_to_state == 'same':
            # Same-state transition
            return to_state == from_state
        elif isinstance(expected_to_state, dict):
            # Conditional transition: resolve based on from_state
            expected = expected_to_state.get(from_state, expected_to_state.get('default', from_state))
            return to_state == expected
        elif isinstance(expected_to_state, str):
            # Simple fixed-state transition
            return to_state == expected_to_state
        else:
            # Unknown format
            return False

    def update_agent_state(self, agent_name: str, trigger: str, action: str = None, host_state_changes: Dict[int, str] = None, action_success: bool = None) -> None:
        """
        Update agent state based on triggers.

        Args:
            agent_name: Name of the agent to update
            trigger: Type of trigger ("successful_action", "host_state_change", "action_result")
            action: The action that was executed
            host_state_changes: Dict of host_id -> new_state for "host_state_change" trigger
            action_success: Whether the action succeeded (for "action_result" trigger)
        """
        if agent_name not in self._agents:
            return

        current_agent_state = self._agents[agent_name]
        agent_config = self.scenario_config.get('Agents', {}).get(agent_name, {})
        transitions = agent_config.get('transitions', {})

        # Handle explicit DFA transitions (action-based)
        for transition_name, transition_config in transitions.items():
            if trigger == "action_result" and action_success is not None:
                # Check if this transition matches the current state and action
                from_state = transition_config.get('from_state')
                required_action = transition_config.get('action')

                if from_state == current_agent_state and required_action == action:
                    # Use on_success or on_failure transitions for explicit DFA
                    if action_success:
                        new_state = transition_config.get('on_success')
                    else:
                        new_state = transition_config.get('on_failure')

                    if new_state:
                        self._agents[agent_name] = new_state
                        return  # State updated, done

        # Handle reactive transitions (environment-triggered)
        reactive_transitions = agent_config.get('reactive_transitions', {})
        for react_name, react_config in reactive_transitions.items():
            if react_config.get('trigger') == trigger:
                # Check from_state constraint
                from_state = react_config.get('from_state')
                if from_state != 'any' and from_state != current_agent_state:
                    continue

                # Evaluate condition based on trigger type
                if trigger == "host_state_change" and host_state_changes:
                    condition = react_config.get('condition', {})
                    if self._evaluate_condition(condition, host_state_changes):
                        new_state = react_config.get('to_state')
                        if new_state:
                            self._agents[agent_name] = new_state
                            return  # State updated, done

    def _evaluate_condition(self, condition: Dict[str, Any], host_state_changes: Dict[int, str]) -> bool:
        """
        Evaluate a reactive transition condition.

        Args:
            condition: Condition definition from YAML
            host_state_changes: Dictionary of host_id -> new_state

        Returns:
            True if condition is met, False otherwise
        """
        condition_type = condition.get('type')

        if condition_type == 'any_host_in_states':
            # Check if any changed host is in one of the specified states
            target_states = condition.get('states', [])
            return any(state in target_states for state in host_state_changes.values())

        elif condition_type == 'all_hosts_in_states':
            # Check if all changed hosts are in one of the specified states
            target_states = condition.get('states', [])
            return all(state in target_states for state in host_state_changes.values())

        elif condition_type == 'specific_host':
            # Check if a specific host reached a specific state
            target_host = condition.get('host_id')
            target_state = condition.get('state')
            return host_state_changes.get(target_host) == target_state

        # Unknown condition type
        return False