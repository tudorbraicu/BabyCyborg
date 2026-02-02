"""
Red team actions for BabyCyborg.

Each action has hard-coded logic for state transitions and rewards.
"""
from typing import TYPE_CHECKING
from .base import Action, ActionResult

if TYPE_CHECKING:
    from ..environment import Environment


class DiscoverRemoteSystems(Action):
    """
    Discover Remote Systems (DRS) - Broadcast discovery action.

    Discovers all hosts in the network (like a ping sweep).
    - Type: Broadcast (affects all hosts conceptually, but doesn't change their state)
    - From: any state
    - To: same (no host state change)
    - Reward: 10 per host
    - ActionSpace: Discovers all hosts
    """

    def execute(self, env: 'Environment') -> ActionResult:
        """Execute DRS - discover all hosts without changing their states."""
        # Check monitors
        allowed, reason = self._check_monitors(env, 'DiscoverRemoteSystems')
        if not allowed:
            env._update_agent_observation(self.agent, f'DiscoverRemoteSystems_{self.host_id}', False)
            current_state = env.get_host_state(self.host_id)
            return ActionResult(False, current_state, 0.0, f"Blocked: {reason}")

        # Calculate reward (10 per host)
        total_reward = 10.0 * env.num_hosts

        # Update ActionSpace - discover all hosts
        action_space = env.get_action_space(self.agent)
        action_space.discover_all_hosts()

        env._update_agent_observation(self.agent, f'DiscoverRemoteSystems_{self.host_id}', True)
        final_state = env.get_host_state(self.host_id)
        return ActionResult(True, final_state, total_reward,
                           f"Discovered {env.num_hosts} hosts on the network")


class DiscoverNetworkServices(Action):
    """
    Discover Network Services (DNS) - Local reconnaissance.

    Scans a specific host for open ports and running services.
    - Type: Local (single host)
    - From: q0 (discovered, secure)
    - To: q1 (services discovered)
    - Reward: 0
    - ActionSpace: Already requires host to be discovered
    """

    def execute(self, env: 'Environment') -> ActionResult:
        """Execute DNS - discover services on a host (q0 → q1, or stay in higher states)."""
        try:
            current_state = env.get_host_state(self.host_id)
        except ValueError as e:
            return ActionResult(False, "unknown", 0.0, str(e))

        # Check monitors
        allowed, reason = self._check_monitors(env, 'DiscoverNetworkServices')
        if not allowed:
            env._update_agent_observation(self.agent, f'DiscoverNetworkServices_{self.host_id}', False)
            return ActionResult(False, current_state, 0.0, f"Blocked: {reason}")

        # Apply state transition: q0 → q1 (forward), otherwise stay
        if current_state == 'q0':
            new_state = 'q1'
        else:
            new_state = current_state  # Stay in current state (backward action allowed)

        env.set_host_state(self.host_id, new_state)

        env._update_agent_observation(self.agent, f'DiscoverNetworkServices_{self.host_id}', True)
        return ActionResult(True, new_state, 0.0, "Network services discovered")


class ExploitRemoteService(Action):
    """
    Exploit Remote Service (ERS) - Initial compromise.

    Exploits a vulnerability in a discovered service to gain initial access.
    - Type: Local (single host)
    - From: q1 (services discovered)
    - To: q2 (exploited, foothold established)
    - Reward: 1
    - ActionSpace: Requires host to be discovered
    """

    def execute(self, env: 'Environment') -> ActionResult:
        """Execute ERS - exploit a service (q1 → q2, or stay in higher states)."""
        try:
            current_state = env.get_host_state(self.host_id)
        except ValueError as e:
            return ActionResult(False, "unknown", 0.0, str(e))

        # Check monitors
        allowed, reason = self._check_monitors(env, 'ExploitRemoteService')
        if not allowed:
            env._update_agent_observation(self.agent, f'ExploitRemoteService_{self.host_id}', False)
            return ActionResult(False, current_state, 0.0, f"Blocked: {reason}")

        # Apply state transition: q1 → q2 (forward), otherwise stay
        if current_state == 'q1':
            new_state = 'q2'
        else:
            new_state = current_state  # Stay in current state (backward action allowed)

        env.set_host_state(self.host_id, new_state)

        env._update_agent_observation(self.agent, f'ExploitRemoteService_{self.host_id}', True)
        return ActionResult(True, new_state, 1.0, "Remote service exploited successfully")


class PrivilegeEscalate(Action):
    """
    Privilege Escalate (PE) - Gain elevated access.

    Escalates from user-level to administrator/root access.
    - Type: Local (single host)
    - From: q2 (exploited)
    - To: q3 (privilege escalated, full control)
    - Reward: 5
    - ActionSpace: Requires host to be discovered
    """

    def execute(self, env: 'Environment') -> ActionResult:
        """Execute PE - escalate privileges (q2 → q3, or stay in q3)."""
        try:
            current_state = env.get_host_state(self.host_id)
        except ValueError as e:
            return ActionResult(False, "unknown", 0.0, str(e))

        # Check monitors
        allowed, reason = self._check_monitors(env, 'PrivilegeEscalate')
        if not allowed:
            env._update_agent_observation(self.agent, f'PrivilegeEscalate_{self.host_id}', False)
            return ActionResult(False, current_state, 0.0, f"Blocked: {reason}")

        # Apply state transition: q2 → q3 (forward), otherwise stay
        if current_state == 'q2':
            new_state = 'q3'
        else:
            new_state = current_state  # Stay in current state (backward action allowed)

        env.set_host_state(self.host_id, new_state)

        env._update_agent_observation(self.agent, f'PrivilegeEscalate_{self.host_id}', True)
        return ActionResult(True, new_state, 5.0, "Privileges escalated to administrator")


class Impact(Action):
    """
    Impact - Execute mission objective.

    Performs the final objective (data exfiltration, service disruption, etc.).
    - Type: Local (single host)
    - From: q3 (privilege escalated)
    - To: q3 (state unchanged)
    - Reward: 20
    - ActionSpace: Requires host to be discovered
    """

    def execute(self, env: 'Environment') -> ActionResult:
        """Execute Impact - achieve mission objective (stays in current state)."""
        try:
            current_state = env.get_host_state(self.host_id)
        except ValueError as e:
            return ActionResult(False, "unknown", 0.0, str(e))

        # Check monitors
        allowed, reason = self._check_monitors(env, 'Impact')
        if not allowed:
            env._update_agent_observation(self.agent, f'Impact_{self.host_id}', False)
            return ActionResult(False, current_state, 0.0, f"Blocked: {reason}")

        # State stays unchanged, but high reward
        new_state = current_state

        env._update_agent_observation(self.agent, f'Impact_{self.host_id}', True)
        return ActionResult(True, new_state, 20.0, "Mission impact achieved")
