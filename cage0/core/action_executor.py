"""
ActionExecutor - Handles action execution and validation.

Separates action logic from the main simulator for better modularity.
"""
from typing import Dict, Any, Tuple, List
from .state_manager import StateManager


class ActionResult:
    """Result of an action execution."""

    def __init__(self, success: bool, new_state: str, reward: float, message: str = ""):
        self.success = success
        self.new_state = new_state
        self.reward = reward
        self.message = message

    def __repr__(self):
        return f"ActionResult(success={self.success}, new_state='{self.new_state}', reward={self.reward})"


class ActionExecutor:
    """Executes and validates agent actions."""

    def __init__(self, scenario_config: Dict[str, Any], state_manager: StateManager):
        """Initialize action executor with scenario configuration."""
        self.scenario_config = scenario_config
        self.state_manager = state_manager

    def execute_action(self, agent: str, action: str, host_id: int) -> ActionResult:
        """
        Execute an action for an agent on a specific host.

        Args:
            agent: Agent name (e.g., 'Red', 'Blue')
            action: Action to execute
            host_id: Target host index

        Returns:
            ActionResult with execution details
        """
        try:
            current_state = self.state_manager.get_host_state(host_id)
        except ValueError as e:
            return ActionResult(False, "unknown", 0.0, str(e))

        # Get action definition
        agent_actions = self.scenario_config.get('Agents', {}).get(agent, {}).get('actions', {})
        action_def = agent_actions.get(action, {})

        if not action_def:
            return ActionResult(False, current_state, 0.0, f"Action '{action}' not defined for agent '{agent}'")

        # Calculate new state and reward
        new_state, reward = self._apply_action_logic(current_state, action_def, action)

        # Validate transition
        if not self.state_manager.can_transition(current_state, new_state, action, agent):
            return ActionResult(False, current_state, 0.0, f"Invalid transition: {current_state} -> {new_state}")

        # Apply the state change
        self.state_manager.set_host_state(host_id, new_state)

        return ActionResult(True, new_state, reward, f"Action '{action}' executed successfully")

    def _apply_action_logic(self, current_state: str, action_def: Dict[str, Any], action: str) -> Tuple[str, float]:
        """
        Apply action logic to determine new state and reward.

        Args:
            current_state: Current host state
            action_def: Action definition from scenario
            action: Action name

        Returns:
            Tuple of (new_state, reward)
        """
        from_state = action_def.get('from_state')
        to_state = action_def.get('to_state')
        reward = action_def.get('reward', 0.0)

        # Check if action is valid for current state
        if from_state != 'any' and from_state != current_state:
            return current_state, 0.0  # Invalid state, no reward

        # Calculate new state
        if to_state == 'same':
            new_state = current_state
        elif to_state == 'q1' and action == 'Remove':
            # Special case for Remove: q0->q0, others->q1
            new_state = 'q0' if current_state == 'q0' else 'q1'
        else:
            new_state = to_state

        return new_state, reward

