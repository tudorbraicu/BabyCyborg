"""
Random Red Agent - Takes random red team actions.
"""
import random
from typing import List, Dict, Any
from .base_agent import BaseAgent


class RandomRedAgent(BaseAgent):
    """Red agent that takes random actions from the available red action set."""

    def __init__(self, name: str = "RandomRed"):
        """
        Initialize the Random Red Agent.

        Args:
            name: Name of the agent
        """
        super().__init__(name)
        self.actions = [
            'DiscoverNetworkServices',
            'ExploitRemoteService',
            'PrivilegeEscalate',
            'Impact'
        ]

    def get_action(self, state_vector: List[str], host_states: Dict[int, str], current_step: int) -> Dict[str, Any]:
        """
        Returns a random red action on a random host.

        Args:
            state_vector: List of host states
            host_states: Dictionary mapping host index to state
            current_step: Current step number

        Returns:
            Dictionary with random action and host
        """
        action = random.choice(self.actions)
        host = random.choice(range(len(state_vector)))
        return {'action': action, 'host': host}