"""
ObservationHandler - Manages agent observations from action results.

This module handles the observation interface between agents and the environment.
Agents receive observations (success/failure) when they execute actions.
"""
from typing import Dict, Any, Optional


class Observation:
    """Represents an observation from an action execution."""

    def __init__(self, success: bool, action: str, message: str = ""):
        """
        Initialize an observation.

        Args:
            success: Whether the action was successful
            action: The action that was executed
            message: Optional message describing the observation
        """
        self.success = success
        self.action = action
        self.message = message

    def __repr__(self):
        return f"Observation(success={self.success}, action='{self.action}')"


class ObservationHandler:
    """Handles agent observations and state updates based on action results."""

    def __init__(self, scenario_config: Dict[str, Any]):
        """
        Initialize observation handler with scenario configuration.

        Args:
            scenario_config: Scenario configuration dictionary
        """
        self.scenario_config = scenario_config
        self.agent_states: Dict[str, str] = {}

    def create_observation(self, action: str, action_success: bool, message: str = "") -> Observation:
        """
        Create an observation from an action result.

        Args:
            action: The action that was executed
            action_success: Whether the action was successful
            message: Optional message about the observation

        Returns:
            Observation object
        """
        return Observation(success=action_success, action=action, message=message)

    def update_agent_state_from_observation(
        self,
        agent_name: str,
        observation: Observation,
        current_agent_state: str
    ) -> Optional[str]:
        """
        Update agent state based on an observation.

        Args:
            agent_name: Name of the agent
            observation: Observation from action execution
            current_agent_state: Current state of the agent

        Returns:
            New agent state if transition occurred, None otherwise
        """
        agent_config = self.scenario_config.get('Agents', {}).get(agent_name, {})
        transitions = agent_config.get('transitions', {})

        # Handle explicit DFA transitions
        if isinstance(transitions, list):
            return self._handle_list_transitions(
                transitions, current_agent_state, observation.action, observation.success
            )
        else:
            # Legacy dict-based format
            return self._handle_dict_transitions(
                transitions, current_agent_state, observation.action, observation.success
            )

    def _handle_list_transitions(
        self,
        transitions: list,
        current_agent_state: str,
        action: str,
        action_success: bool
    ) -> Optional[str]:
        """Handle list-based transition format."""
        waiting_state = None

        # Find send transition
        for transition in transitions:
            from_state = transition.get('from_state')
            trans_label = transition.get('transition', '')

            if trans_label.startswith('!'):
                action_str = trans_label[1:]
                parts = action_str.split('_')
                if len(parts) >= 3:
                    # Include host in action_name for proper matching
                    # e.g., "Red_DiscoverNetworkServices_3" -> "DiscoverNetworkServices_3"
                    action_name = '_'.join(parts[1:])
                else:
                    action_name = action_str

                if from_state == current_agent_state and action_name == action:
                    waiting_state = transition.get('to_state')
                    break

        if waiting_state:
            # Find receive transition
            target_transition = "?success" if action_success else "?failure"
            for transition in transitions:
                if (transition.get('from_state') == waiting_state and
                    transition.get('transition') == target_transition):
                    return transition.get('to_state')

        return None

    def _handle_dict_transitions(
        self,
        transitions: Dict[str, Any],
        current_agent_state: str,
        action: str,
        action_success: bool
    ) -> Optional[str]:
        """Handle dict-based transition format (legacy)."""
        for transition_name, transition_config in transitions.items():
            from_state = transition_config.get('from_state')
            required_action = transition_config.get('action')

            if required_action and required_action.startswith('!'):
                required_action = required_action[1:]

            if required_action:
                parts = required_action.split('_')
                if len(parts) >= 3:
                    # Include host in action_name for proper matching
                    action_name = '_'.join(parts[1:])
                else:
                    action_name = required_action
            else:
                action_name = None

            if from_state == current_agent_state and action_name == action:
                on_transitions = transition_config.get('on') or transition_config.get(True)
                if on_transitions:
                    target_transition = "?success" if action_success else "?failure"
                    for on_trans in on_transitions:
                        if on_trans.get('transition') == target_transition:
                            return on_trans.get('to_state')
                else:
                    if action_success:
                        return transition_config.get('on_success')
                    else:
                        return transition_config.get('on_failure')

        return None

    def reset(self):
        """Reset observation handler state."""
        self.agent_states.clear()
