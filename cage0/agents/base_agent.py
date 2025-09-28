"""
Base agent class for Cage0 simulator.
"""
from typing import List, Dict, Any


class BaseAgent:
    """Base agent class that all other agents inherit from."""

    def __init__(self, name: str):
        """
        Initialize the base agent.

        Args:
            name: Name of the agent (e.g., "Red", "Blue")
        """
        self.name = name

    def get_action(self, state_vector: List[str], host_states: Dict[int, str], current_step: int) -> Dict[str, Any]:
        """
        Get action given current state.

        Args:
            state_vector: List of host states (e.g., ['q0', 'q1', 'q0', 'q0'])
            host_states: Dictionary mapping host index to state (e.g., {0: 'q0', 1: 'q1'})
            current_step: Current step number in the simulation

        Returns:
            Dictionary with 'action' and 'host' keys
        """
        raise NotImplementedError("Subclasses must implement get_action method")

    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}')"