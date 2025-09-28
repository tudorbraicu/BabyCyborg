"""
Proactive Blue Agent - Removes any non-secure hosts immediately.
"""
from typing import List, Dict, Any
from .base_agent import BaseAgent


class ProactiveBlueAgent(BaseAgent):
    """
    Blue agent that proactively removes any discovered services or compromises.

    Removes any host that's not in secure state q0.
    """

    def __init__(self, name: str = "ProactiveBlue"):
        """
        Initialize the Proactive Blue Agent.

        Args:
            name: Name of the agent
        """
        super().__init__(name)

    def get_action(self, state_vector: List[str], host_states: Dict[int, str], current_step: int) -> Dict[str, Any]:
        """
        Remove any host that's not in secure state q0.

        Args:
            state_vector: List of host states
            host_states: Dictionary mapping host index to state
            current_step: Current step number

        Returns:
            Dictionary with Remove action on most compromised host, or NoOp if all secure
        """
        host_states = {i: state for i, state in enumerate(state_vector)}

        # Find any non-secure hosts
        compromised_hosts = [host for host, state in host_states.items() if state != 'q0']

        if compromised_hosts:
            # Remove most compromised first
            threat_levels = {'q0': 0, 'q1': 1, 'q2': 2, 'q3': 3}
            most_compromised = max(compromised_hosts,
                                 key=lambda h: threat_levels.get(host_states[h], 0))
            return {'action': 'Remove', 'host': most_compromised}

        # All hosts secure, do nothing
        return {'action': 'NoOp', 'host': 0}