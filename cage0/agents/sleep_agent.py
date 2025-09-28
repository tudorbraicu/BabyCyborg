"""
Sleep Agent - Does nothing (NoOp/Sleep actions only).
"""
from typing import List, Dict, Any
from .base_agent import BaseAgent


class SleepAgent(BaseAgent):
    """Agent that always sleeps/does nothing."""

    def __init__(self, name: str = "SleepAgent"):
        """
        Initialize the Sleep Agent.

        Args:
            name: Name of the agent
        """
        super().__init__(name)

    def get_action(self, state_vector: List[str], host_states: Dict[int, str], current_step: int) -> Dict[str, Any]:
        """
        Always returns NoOp action on host 0.

        Args:
            state_vector: List of host states
            host_states: Dictionary mapping host index to state
            current_step: Current step number

        Returns:
            Dictionary with NoOp action on host 0
        """
        return {'action': 'NoOp', 'host': 0}