"""
Modular BabyCyborg Simulator - Refactored architecture.

This replaces the monolithic Cage0Sim with a modular design using:
- StateManager: Host and agent state management
- ActionExecutor: Action execution and validation
- RewardCalculator: Reward calculation and tracking

Supports YAML-defined agent DFAs alongside host DFAs.
Maintains compatibility with the original Cage0Sim interface.
"""
import yaml
from typing import List, Dict, Any, Optional
from .core import StateManager, ActionExecutor, RewardCalculator
from .agents.agent_generator import create_agents_from_yaml


class ModularCage0Sim:
    """Modular BabyCyborg simulation environment."""

    def __init__(self, scenario_path: str, max_steps: int = 20):
        """Initialize the modular simulation environment."""
        with open(scenario_path, 'r') as f:
            self.scenario_config = yaml.safe_load(f)

        # Initialize modular components
        self.state_manager = StateManager(self.scenario_config)
        self.action_executor = ActionExecutor(self.scenario_config, self.state_manager)
        self.reward_calculator = RewardCalculator(self.scenario_config)

        # Simulation state
        self.max_steps = max_steps
        self._t = 0
        self._current_agent = 'Red'
        self._trace: List[Dict[str, Any]] = []

        # Legacy compatibility properties
        self.num_hosts = self.state_manager.num_hosts
        self.host_names = self.state_manager.host_names
        self._agents = self.scenario_config['Agents']

        # YAML-based agent instances (optional)
        self.yaml_agents: Dict[str, Any] = {}

    def reset(self) -> List[str]:
        """Reset environment to initial state."""
        self.state_manager.reset()
        self.reward_calculator.reset()
        self._t = 0
        self._current_agent = 'Red'
        self._trace = []
        return self.state_manager.get_state_vector()

    def step(self, action: str, host: int, opponent_action: str = None, opponent_host: int = None) -> Dict[str, Any]:
        """Execute one simulation step: handles both agents' actions in one step."""
        assert 0 <= host < self.num_hosts, f"bad host index: {host}"

        # Store initial agent
        initial_agent = self._current_agent

        # Execute current agent's action
        result = self.action_executor.execute_action(self._current_agent, action, host)
        reward = result.reward if result.success else 0.0

        # Record reward and trace
        self.reward_calculator.record_reward(
            self._current_agent, action, host, reward, self._t,
            {'success': result.success, 'message': result.message}
        )

        current_agent_trace = {
            'agent': self._current_agent[0],  # 'R' or 'B'
            'action': action,
            'host': host,
            'reward': reward
        }

        # Switch to opponent
        opponent_agent = 'Blue' if self._current_agent == 'Red' else 'Red'
        self._current_agent = opponent_agent

        # Execute opponent action
        if opponent_action is not None and opponent_host is not None:
            assert 0 <= opponent_host < self.num_hosts, f"bad opponent host index: {opponent_host}"
            opp_result = self.action_executor.execute_action(opponent_agent, opponent_action, opponent_host)
            opp_reward = opp_result.reward if opp_result.success else 0.0
        else:
            # Default opponent action (Sleep/no-op)
            opponent_action = 'Sleep'
            opponent_host = 0
            opp_reward = 0.0

        # Record opponent reward and trace
        self.reward_calculator.record_reward(
            opponent_agent, opponent_action, opponent_host, opp_reward, self._t,
            {'success': True, 'message': 'Default action'}
        )

        opponent_trace = {
            'agent': opponent_agent[0],  # 'R' or 'B'
            'action': opponent_action,
            'host': opponent_host,
            'reward': opp_reward
        }

        # Add both actions to trace
        self._trace.append(current_agent_trace)
        self._trace.append(opponent_trace)

        # Advance time
        self._t += 1
        done = self._t >= self.max_steps

        # Return to the agent that should act next
        self._current_agent = 'Blue' if initial_agent == 'Red' else 'Red'

        return {
            'state_vector': self.state_manager.get_state_vector(),
            'reward': reward,
            'opponent_reward': opp_reward,
            'total_step_reward': reward + opp_reward,
            'done': done,
            'total_reward': self.reward_calculator.get_total_reward(),
            'current_agent': self._current_agent,
            'last_actions': {
                initial_agent: {'action': action, 'host': host, 'reward': reward},
                opponent_agent: {'action': opponent_action, 'host': opponent_host, 'reward': opp_reward}
            }
        }

    def get_current_agent(self) -> str:
        """Get the agent whose turn it is to act."""
        return self._current_agent

    def get_total_reward(self) -> float:
        """Get the cumulative total reward."""
        return self.reward_calculator.get_total_reward()

    def get_trace(self) -> List[Dict[str, Any]]:
        """Get the simple trace: Agent, action, host, reward."""
        return self._trace.copy()

    def get_last_action(self, agent: str) -> Dict[str, Any]:
        """Get the last action taken by a specific agent."""
        agent_letter = agent[0].upper()

        for trace_entry in reversed(self._trace):
            if trace_entry['agent'] == agent_letter:
                return {
                    'action': trace_entry['action'],
                    'host': trace_entry['host'],
                    'reward': trace_entry['reward']
                }

        return None

    def get_last_actions(self) -> Dict[str, Dict[str, Any]]:
        """Get the last actions for both agents."""
        return {
            'Red': self.get_last_action('Red'),
            'Blue': self.get_last_action('Blue')
        }


    def get_reward_summary(self) -> Dict[str, Any]:
        """Get detailed reward statistics."""
        return self.reward_calculator.get_reward_summary()

    def create_yaml_agents(self) -> Dict[str, Any]:
        """
        Create YAML-based agent instances from the scenario configuration.

        Returns:
            Dictionary mapping agent names to generated agent instances
        """
        self.yaml_agents = create_agents_from_yaml(self.scenario_config, self.state_manager)
        return self.yaml_agents

    def get_yaml_agent(self, agent_name: str) -> Optional[Any]:
        """
        Get a YAML-based agent instance.

        Args:
            agent_name: Name of the agent ('Red', 'Blue', etc.)

        Returns:
            Generated agent instance or None if not found
        """
        if agent_name not in self.yaml_agents:
            # Try to create agents if not already created
            if not self.yaml_agents:
                self.create_yaml_agents()
        return self.yaml_agents.get(agent_name)

    def get_agent_states(self) -> Dict[str, str]:
        """
        Get current states of all agents.

        Returns:
            Dictionary mapping agent names to their current states
        """
        return {name: self.state_manager.get_agent_state(name) for name in self.state_manager.agent_names}

    def auto_step(self) -> Dict[str, Any]:
        """
        Execute one simulation step using YAML-generated agents.

        This high-level method automatically queries both agents for their
        actions and executes them, eliminating the need for external
        action selection.

        Returns:
            Same format as step() method
        """
        # Ensure YAML agents are created
        if not self.yaml_agents:
            self.create_yaml_agents()

        # Get action from current agent
        current_agent_name = self._current_agent
        current_agent = self.get_yaml_agent(current_agent_name)
        current_action_dict = current_agent.get_action(self._t)

        # Get action from opponent agent
        opponent_name = 'Blue' if current_agent_name == 'Red' else 'Red'
        opponent_agent = self.get_yaml_agent(opponent_name)
        opponent_action_dict = opponent_agent.get_action(self._t)

        # Execute the step
        return self.step(
            action=current_action_dict['action'],
            host=current_action_dict['host'],
            opponent_action=opponent_action_dict['action'],
            opponent_host=opponent_action_dict['host']
        )



    # Legacy compatibility - delegate to original method names
    def _apply_action(self, agent: str, state: str, action: str) -> tuple[str, float]:
        """Legacy compatibility method - delegates to ActionExecutor."""
        # Find a host with the given state for compatibility
        for host_id in range(self.state_manager.num_hosts):
            host_state = self.state_manager.get_host_state(host_id)
            if host_state == state:
                result = self.action_executor.execute_action(agent, action, host_id)
                return result.new_state, result.reward

        return state, 0.0  # No matching host found

    @property
    def _hosts(self) -> List[str]:
        """Legacy compatibility property."""
        return self.state_manager.get_state_vector()

    @property
    def _total_reward(self) -> float:
        """Legacy compatibility property."""
        return self.reward_calculator.get_total_reward()