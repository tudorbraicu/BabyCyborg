"""
RemoveHost0Blue - Blue agent that only does Remove on Host_0 or NoOp.

This agent randomly chooses between:
- Remove on Host_0 (50%)
- NoOp (50%)
"""
import random
from typing import Dict, Any
from .base_agent import BaseAgent


class RemoveHost0BlueAgent(BaseAgent):
    """
    Blue agent that only performs Remove on Host_0 or NoOp.
    """

    def __init__(self, name: str = "Blue"):
        """
        Initialize the agent.

        Args:
            name: Agent name (default "Blue")
        """
        super().__init__(name)

    def reset(self):
        """Reset agent state for a new episode."""
        pass  # No state to reset

    def get_action(self, current_step: int) -> Dict[str, Any]:
        """
        Get the next action: either Remove on Host_0 or NoOp.

        Args:
            current_step: Current step number (unused)

        Returns:
            Dictionary with 'action' key in format "Blue_ActionName_HostId"
        """
        if random.random() < 0.5:
            return {'action': f'{self.name}_Remove_0'}
        else:
            return {'action': f'{self.name}_NoOp_0'}

    def __repr__(self):
        return f"RemoveHost0BlueAgent()"


def create_remove_host0_blue() -> RemoveHost0BlueAgent:
    """Factory function to create a RemoveHost0Blue agent."""
    return RemoveHost0BlueAgent(name="Blue")
