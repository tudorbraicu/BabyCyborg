"""
Reactive Blue Agent - Removes threats when they reach a certain threshold.
"""
from typing import List, Dict, Any
from .base_agent import BaseAgent


class ReactiveBlueAgent(BaseAgent):
    """
    Blue agent that reactively removes threats when hosts become too compromised.

    Default behavior: Remove when hosts reach q2 (exploited) or higher.
    """

    def __init__(self, name: str = "ReactiveBlue", remove_threshold: str = 'q2'):
        """
        Initialize the Reactive Blue Agent.

        Args:
            name: Name of the agent
            remove_threshold: State at which to start removing threats (default: 'q2')
        """
        super().__init__(name)
        self.remove_threshold = remove_threshold

    def get_action(self, state_vector: List[str], host_states: Dict[int, str], current_step: int) -> Dict[str, Any]:
        """
        Remove threats when hosts become too compromised.

        Args:
            state_vector: List of host states
            host_states: Dictionary mapping host index to state
            current_step: Current step number

        Returns:
            Dictionary with Remove action on most compromised host, or NoOp if no threats
        """
        host_states = {i: state for i, state in enumerate(state_vector)}

        # Define threat levels
        threat_levels = {'q0': 0, 'q1': 1, 'q2': 2, 'q3': 3}
        threshold_level = threat_levels.get(self.remove_threshold, 2)

        # Find hosts that need remediation
        threatening_hosts = [
            host for host, state in host_states.items()
            if threat_levels.get(state, 0) >= threshold_level
        ]

        if threatening_hosts:
            # Remove threat from most compromised host first
            most_compromised = max(threatening_hosts,
                                 key=lambda h: threat_levels.get(host_states[h], 0))
            return {'action': 'Remove', 'host': most_compromised}

        # No immediate threats, do nothing
        return {'action': 'NoOp', 'host': 0}