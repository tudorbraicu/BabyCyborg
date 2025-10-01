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

    def get_action(self, current_step: int) -> Dict[str, Any]:
        """
        Get action based on agent's current DFA state from StateManager.

        The agent queries its current state from StateManager and returns
        the appropriate action. The agent does NOT update its own state—
        that's StateManager's job after the action is executed.

        Args:
            current_step: Current step number in the simulation

        Returns:
            Dictionary with 'action' and 'host' keys
        """
        raise NotImplementedError("Subclasses must implement get_action method")

    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}')"