"""
Blue team (defender) actions for BabyCyborg.

Each action has hard-coded logic for state transitions and rewards.
"""
from typing import TYPE_CHECKING
from .base import Action, ActionResult

if TYPE_CHECKING:
    from ..environment import Environment


class NoOp(Action):
    """
    No Operation (NoOp) - Do nothing.

    Blue agent takes no action this turn.
    - Type: Local (targets a host but doesn't affect it)
    - From: any state
    - To: same (no change)
    - Reward: 0
    - ActionSpace: Doesn't require host to be discovered
    """

    def execute(self, env: 'Environment') -> ActionResult:
        """Execute NoOp - do nothing."""
        try:
            current_state = env.get_host_state(self.host_id)
        except ValueError as e:
            return ActionResult(False, "unknown", 0.0, str(e))

        # Check monitors (even though NoOp shouldn't be blocked)
        allowed, reason = self._check_monitors(env, 'NoOp')
        if not allowed:
            env._update_agent_observation(self.agent, f'NoOp_{self.host_id}', False)
            return ActionResult(False, current_state, 0.0, f"Blocked: {reason}")

        # No state change
        env._update_agent_observation(self.agent, f'NoOp_{self.host_id}', True)
        return ActionResult(True, current_state, 0.0, "No operation performed")


class Remove(Action):
    """
    Remove - Remediate compromised host.

    Blue agent removes Red's access and restores the host to secure state.
    - Type: Local (single host)
    - From: any state
    - To: q0 (restored to secure state)
    - Reward: 0
    - ActionSpace: Requires host to be discovered by Blue

    Note: If host is already at q0, stays at q0 (idempotent).
    """

    def execute(self, env: 'Environment') -> ActionResult:
        """Execute Remove - restore host to q0."""
        try:
            current_state = env.get_host_state(self.host_id)
        except ValueError as e:
            return ActionResult(False, "unknown", 0.0, str(e))

        # Check monitors
        allowed, reason = self._check_monitors(env, 'Remove')
        if not allowed:
            env._update_agent_observation(self.agent, f'Remove_{self.host_id}', False)
            return ActionResult(False, current_state, 0.0, f"Blocked: {reason}")

        # Apply state transition: any → q0
        new_state = 'q0'
        env.set_host_state(self.host_id, new_state)

        # Message depends on whether it was a change
        if current_state == 'q0':
            message = "Host already secure (no change)"
        else:
            message = f"Host remediated ({current_state} → q0)"

        env._update_agent_observation(self.agent, f'Remove_{self.host_id}', True)
        return ActionResult(True, new_state, 0.0, message)
