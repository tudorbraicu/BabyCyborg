"""
Environment - Manages state and executes actions.

The game world: stores host/agent states and executes action transitions.
"""
from typing import List, Dict, Any
from .observation import ObservationHandler
from .action import LocalAction, BroadcastAction, ActionResult  # Keep for backwards compatibility
from .action_space import ActionSpace
from .actions import ALL_ACTIONS, RED_ACTIONS, BLUE_ACTIONS


class Environment:
    """Manages state and executes actions."""

    def __init__(self, scenario_config: Dict[str, Any], referee=None):
        """Initialize environment with scenario configuration."""
        self.scenario_config = scenario_config
        self.referee = referee

        # Host state
        self.num_hosts = scenario_config['Topology']['num_hosts']
        self.host_names = scenario_config['Topology']['hosts']
        self.initial_states = self._extract_initial_states()
        self.host_ip_addresses = self._extract_host_ip_addresses()
        self._hosts: List[str] = []

        # Agent state
        self.agent_names = list(scenario_config.get('Agents', {}).keys())
        self.agent_initial_states = self._extract_agent_initial_states()
        self._agents: Dict[str, str] = {}

        # Action spaces - track what each agent knows
        self.action_spaces: Dict[str, ActionSpace] = {}
        self._initialize_action_spaces()

        # Observation handler
        self.observation_handler = ObservationHandler(scenario_config)

    def _extract_initial_states(self) -> List[str]:
        """Extract initial states for each host from scenario."""
        hosts_config = self.scenario_config.get('Hosts', {})
        initial_states = []

        for host_name in self.host_names:
            host_config = hosts_config.get(host_name, {})
            initial_state = host_config.get('initial_state', 'q0')
            initial_states.append(initial_state)

        return initial_states

    def _extract_agent_initial_states(self) -> Dict[str, str]:
        """Extract initial states for each agent from scenario."""
        agents_config = self.scenario_config.get('Agents', {})
        agent_initial_states = {}

        for agent_name, agent_config in agents_config.items():
            initial_state = agent_config.get('initial_state', 'p0')
            agent_initial_states[agent_name] = initial_state

        return agent_initial_states

    def _extract_host_ip_addresses(self) -> List[str]:
        """Extract IP addresses for each host from scenario."""
        hosts_config = self.scenario_config.get('Hosts', {})
        ip_addresses = []

        for host_name in self.host_names:
            host_config = hosts_config.get(host_name, {})
            ip_address = host_config.get('ip_address', '0.0.0.0')
            ip_addresses.append(ip_address)

        return ip_addresses

    def _initialize_action_spaces(self) -> None:
        """Initialize ActionSpace for each agent."""
        agents_config = self.scenario_config.get('Agents', {})

        for agent_name, agent_config in agents_config.items():
            # Use hard-coded action sets instead of YAML
            if agent_name == 'Red':
                allowed_actions = RED_ACTIONS
            elif agent_name == 'Blue':
                allowed_actions = BLUE_ACTIONS
            else:
                # Unknown agent, give empty action set
                allowed_actions = {}

            action_space = ActionSpace(agent_name, self.num_hosts, allowed_actions)

            # Initial host discovery
            # Blue (defender) knows all hosts from the start
            # Red (attacker) only knows their start host
            if agent_name == 'Blue':
                action_space.discover_all_hosts()
            else:
                start_host = agent_config.get('start_host', 0)
                if start_host is not None:
                    action_space.discover_host(start_host)

            self.action_spaces[agent_name] = action_space

    def get_host_ip_address(self, host_id: int) -> str:
        """Get the IP address of a specific host."""
        if 0 <= host_id < len(self.host_ip_addresses):
            return self.host_ip_addresses[host_id]
        return '0.0.0.0'

    def reset(self) -> List[str]:
        """Reset all hosts and agents to their initial states."""
        self._hosts = self.initial_states.copy()
        self._agents = self.agent_initial_states.copy()

        # Reset action spaces
        for agent_name, action_space in self.action_spaces.items():
            action_space.reset()
            # Blue (defender) knows all hosts from the start
            # Red (attacker) only knows their start host
            if agent_name == 'Blue':
                action_space.discover_all_hosts()
            else:
                agent_config = self.scenario_config.get('Agents', {}).get(agent_name, {})
                start_host = agent_config.get('start_host', 0)
                if start_host is not None:
                    action_space.discover_host(start_host)

        return self.get_state_vector()

    def get_state_vector(self) -> List[str]:
        state_vector = self._hosts.copy()
        for agent_name in self.agent_names:
            state_vector.append(self._agents.get(agent_name, 'p0'))
        return state_vector

    def get_host_state(self, host_id: int) -> str:
        if 0 <= host_id < len(self._hosts):
            return self._hosts[host_id]
        raise ValueError(f"Invalid host_id: {host_id}")

    def set_host_state(self, host_id: int, new_state: str) -> None:
        if 0 <= host_id < len(self._hosts):
            self._hosts[host_id] = new_state
        else:
            raise ValueError(f"Invalid host_id: {host_id}")

    def get_agent_state(self, agent_name: str) -> str:
        if agent_name in self._agents:
            return self._agents[agent_name]
        raise ValueError(f"Invalid agent_name: {agent_name}")

    def set_agent_state(self, agent_name: str, new_state: str) -> None:
        if agent_name in self.agent_names:
            self._agents[agent_name] = new_state
        else:
            raise ValueError(f"Invalid agent_name: {agent_name}")

    def get_action_space(self, agent_name: str) -> ActionSpace:
        """
        Get the ActionSpace for a specific agent.

        Args:
            agent_name: Name of the agent

        Returns:
            ActionSpace for the agent
        """
        if agent_name not in self.action_spaces:
            raise ValueError(f"No ActionSpace for agent: {agent_name}")
        return self.action_spaces[agent_name]

    def execute_action(self, agent: str, action: str, host_id: int) -> ActionResult:
        """
        Execute an action for an agent on a specific host.

        Uses concrete action classes (DiscoverRemoteSystems, ExploitRemoteService, etc.)
        instead of YAML-driven generic actions.

        Args:
            agent: Agent name (e.g., 'Red', 'Blue')
            action: Action name (e.g., 'DiscoverRemoteSystems', 'Remove')
            host_id: Target host index

        Returns:
            ActionResult with execution details
        """
        try:
            current_state = self.get_host_state(host_id)
        except ValueError as e:
            return ActionResult(False, "unknown", 0.0, str(e))

        # Get the action class for this action
        action_class = ALL_ACTIONS.get(action)

        if not action_class:
            self._update_agent_observation(agent, action, False)
            return ActionResult(False, current_state, 0.0,
                               f"Unknown action '{action}' (available: {list(ALL_ACTIONS.keys())})")

        # Verify agent is allowed to use this action
        if agent == 'Red' and action not in RED_ACTIONS:
            self._update_agent_observation(agent, action, False)
            return ActionResult(False, current_state, 0.0,
                               f"Action '{action}' not available for Red agent")
        elif agent == 'Blue' and action not in BLUE_ACTIONS:
            self._update_agent_observation(agent, action, False)
            return ActionResult(False, current_state, 0.0,
                               f"Action '{action}' not available for Blue agent")

        # Check ActionSpace - can this agent perform this action on this host?
        action_space = self.get_action_space(agent)

        # Special case: Broadcast actions (DRS) and NoOp don't require host discovery
        if action in ['DiscoverRemoteSystems', 'NoOp']:
            can_perform = True
            reason = "Broadcast/NoOp action allowed"
        else:
            can_perform, reason = action_space.can_perform_action(action, host_id)

        if not can_perform:
            self._update_agent_observation(agent, action, False)
            return ActionResult(False, current_state, 0.0, reason)

        # Create and execute the concrete action object
        action_obj = action_class(agent=agent, host_id=host_id)
        return action_obj.execute(self)

    def _update_agent_observation(self, agent_name: str, action: str, action_success: bool) -> None:
        """
        Update agent state based on observation from action result.

        Args:
            agent_name: Name of the agent
            action: Action that was executed
            action_success: Whether the action was successful
        """
        if agent_name not in self._agents:
            return

        current_agent_state = self._agents[agent_name]

        # Create observation
        observation = self.observation_handler.create_observation(
            action=action,
            action_success=action_success,
            message="Action observation"
        )

        # Update agent state based on observation
        new_state = self.observation_handler.update_agent_state_from_observation(
            agent_name=agent_name,
            observation=observation,
            current_agent_state=current_agent_state
        )

        if new_state:
            self._agents[agent_name] = new_state
