"""
Base action classes for BabyCyborg.

Provides the foundation for all concrete action implementations.
"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..environment import Environment


class ActionResult:
    """Result of an action execution."""

    def __init__(self, success: bool, new_state: str, reward: float, message: str = ""):
        self.success = success
        self.new_state = new_state
        self.reward = reward
        self.message = message

    def __repr__(self):
        return f"ActionResult(success={self.success}, new_state='{self.new_state}', reward={self.reward})"


class Action:
    """
    Base class for all actions.

    Each concrete action (DRS, DNS, ERS, etc.) inherits from this and implements:
    - Hard-coded logic for state transitions
    - Specific reward values
    - ActionSpace updates (if needed)

    Similar to CybORG's action class hierarchy.
    """

    def __init__(self, agent: str, host_id: int):
        """
        Initialize an action.

        Args:
            agent: Name of the agent executing the action
            host_id: Target host index
        """
        self.agent = agent
        self.host_id = host_id

    def execute(self, env: 'Environment') -> ActionResult:
        """
        Execute the action.

        Args:
            env: Environment instance to execute the action in

        Returns:
            ActionResult with execution details
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement execute()")

    def _check_monitors(self, env: 'Environment', action_name: str) -> tuple[bool, str]:
        """
        Check if monitors approve this action.

        Args:
            env: Environment instance
            action_name: Name of the action for monitor evaluation

        Returns:
            Tuple of (allowed, reason)
        """
        if env.referee and env.referee.monitors:
            return env.referee.evaluate_via_monitors(self.agent, action_name, self.host_id)
        return True, "No monitors"

    def __repr__(self):
        return f"{self.__class__.__name__}(agent='{self.agent}', host_id={self.host_id})"
