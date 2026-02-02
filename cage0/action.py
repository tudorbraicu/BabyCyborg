"""
Action - Hierarchy of action classes for executing different action types.

This module provides a class hierarchy for different action types,
similar to CybORG's action class hierarchy.
"""
from typing import Dict, Any, Tuple


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

    Actions encapsulate the logic for executing different types of operations
    in the simulation environment.
    """

    def __init__(self, agent: str, action: str, action_def: Dict[str, Any], host_id: int):
        """
        Initialize an action.

        Args:
            agent: Name of the agent executing the action
            action: Name of the action
            action_def: Action definition from scenario config
            host_id: Target host index
        """
        self.agent = agent
        self.action = action
        self.action_def = action_def
        self.host_id = host_id

    def execute(self, env) -> ActionResult:
        """
        Execute the action.

        Args:
            env: Environment instance to execute the action in

        Returns:
            ActionResult with execution details
        """
        raise NotImplementedError("Subclasses must implement execute()")

    def _apply_action_logic(self, current_state: str) -> Tuple[str, float]:
        """
        Apply action logic to determine new state and reward.

        Args:
            current_state: Current state of the target

        Returns:
            Tuple of (new_state, reward)
        """
        from_state = self.action_def.get('from_state')
        to_state = self.action_def.get('to_state')
        reward = self.action_def.get('reward', 0.0)

        if from_state != 'any' and from_state != current_state:
            return current_state, 0.0

        if to_state == 'same':
            new_state = current_state
        elif isinstance(to_state, dict):
            new_state = to_state.get(current_state, to_state.get('default', current_state))
        elif isinstance(to_state, str):
            new_state = to_state
        else:
            new_state = current_state

        return new_state, reward


class LocalAction(Action):
    """
    Local action: affects a single host.

    Executes on a specific host, calculates the new state, validates with monitors,
    and applies the change if allowed.
    """

    def execute(self, env) -> ActionResult:
        """
        Execute local action on a single host.

        Args:
            env: Environment instance

        Returns:
            ActionResult with execution details
        """
        try:
            current_state = env.get_host_state(self.host_id)
        except ValueError as e:
            return ActionResult(False, "unknown", 0.0, str(e))

        # Calculate what the new state would be (don't apply yet)
        new_state, reward = self._apply_action_logic(current_state)

        # Ask monitors for approval
        if env.referee and env.referee.monitors:
            allowed, reason = env.referee.evaluate_via_monitors(self.agent, self.action, self.host_id)

            if not allowed:
                # Monitors blocked - don't apply the change
                env._update_agent_observation(self.agent, self.action, False)
                return ActionResult(False, current_state, 0.0, f"Blocked: {reason}")

        # Monitors approved (or no monitors) - apply the change
        env.set_host_state(self.host_id, new_state)

        # Update ActionSpace for local discovery actions (e.g., DiscoverNetworkServices)
        # Note: The host should already be discovered to reach this point, but this
        # ensures the ActionSpace is updated if needed
        if 'Discover' in self.action:
            action_space = env.get_action_space(self.agent)
            action_space.discover_host(self.host_id)

        env._update_agent_observation(self.agent, self.action, True)
        return ActionResult(True, new_state, reward, f"Action '{self.action}' executed successfully")


class BroadcastAction(Action):
    """
    Broadcast action: affects all hosts in the network.

    Executes on all hosts, calculates changes for each, validates with monitors,
    and applies all changes if allowed.

    # in the future blue needs to be able to query.
    # game keeping track of what red knows vs red keeping track of what it knows
    """

    def execute(self, env) -> ActionResult:
        """
        Execute broadcast action on all hosts.

        Args:
            env: Environment instance

        Returns:
            ActionResult with execution details
        """
        total_reward = 0.0
        planned_changes = {}  # host_id -> new_state
        affected_hosts = []

        # Calculate what would change for each host (don't apply yet)
        for h_id in range(env.num_hosts):
            current_host_state = env.get_host_state(h_id)
            new_state, reward = self._apply_action_logic(current_host_state)

            if new_state != current_host_state:
                planned_changes[h_id] = new_state
                affected_hosts.append(h_id)
            total_reward += reward

        # Ask monitors for approval
        if env.referee and env.referee.monitors:
            allowed, reason = env.referee.evaluate_via_monitors(self.agent, self.action, self.host_id)

            if not allowed:
                # Monitors blocked - don't apply any changes
                env._update_agent_observation(self.agent, self.action, False)
                current_state = env.get_host_state(self.host_id)
                return ActionResult(False, current_state, 0.0, f"Blocked: {reason}")

        # Monitors approved (or no monitors) - apply all changes
        for h_id, new_state in planned_changes.items():
            env.set_host_state(h_id, new_state)

        # Update ActionSpace for discovery actions (e.g., DiscoverRemoteSystems)
        # Discovery actions reveal hosts without changing their state
        if 'Discover' in self.action:
            action_space = env.get_action_space(self.agent)
            action_space.discover_all_hosts()

        env._update_agent_observation(self.agent, self.action, True)

        message = f"Broadcast action '{self.action}' executed on all hosts (affected: {affected_hosts})"
        final_state = env.get_host_state(self.host_id)
        return ActionResult(True, final_state, total_reward, message)
