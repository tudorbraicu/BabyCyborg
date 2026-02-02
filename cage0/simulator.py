"""
BabyCyborg Simulator - Main interface for running simulations.

Loads YAML configurations and orchestrates the simulation.
"""
import yaml
from typing import List, Dict, Any, Optional
from pathlib import Path
from .environment import Environment
from .action import ActionResult
from .monitors import Referee
from .reward_calculator import RewardCalculator
from .agents.agent_generator import create_agents_from_yaml


def load_modular_scenario(scenario_path: str, agent_overrides: Dict[str, str] = None) -> tuple[Dict[str, Any], Path]:
    """
    Load a scenario configuration, supporting both modular and monolithic formats.

    Args:
        scenario_path: Path to the main scenario YAML file
        agent_overrides: Optional dict mapping agent names to agent file paths

    Returns:
        Tuple of (merged scenario configuration dictionary, resolved scenario path)
    """
    scenario_path = Path(scenario_path)

    # Handle backward compatibility: check if old paths need to be redirected
    if not scenario_path.exists():
        # Try common path migrations
        if str(scenario_path).startswith('scenarios/'):
            # Old structure: scenarios/cage0_scenario.yaml -> yaml_files/config/cage0_scenario.yaml
            new_path = Path('yaml_files') / 'config' / scenario_path.name
            if new_path.exists():
                print(f"Note: Redirecting '{scenario_path}' to '{new_path}'")
                scenario_path = new_path
            else:
                raise FileNotFoundError(
                    f"Scenario file not found at '{scenario_path}' or '{new_path}'. "
                    f"Please use the new path format: 'yaml_files/config/{scenario_path.name}'"
                )
        else:
            raise FileNotFoundError(f"Scenario file not found: '{scenario_path}'")

    scenario_dir = scenario_path.parent

    with open(scenario_path, 'r') as f:
        main_config = yaml.safe_load(f)

    # Apply agent overrides if provided
    if agent_overrides:
        if 'agents' not in main_config:
            main_config['agents'] = {}
        main_config['agents'].update(agent_overrides)

    # Check if this is a modular configuration
    if 'network' in main_config and 'agents' in main_config:
        # Modular format: load and merge referenced files
        merged_config = {}

        # Load network configuration
        network_path = scenario_dir / main_config['network']
        with open(network_path, 'r') as f:
            network_config = yaml.safe_load(f)

        # Merge network config
        merged_config['States'] = network_config.get('States', [])
        merged_config['Hosts'] = network_config.get('Hosts', {})
        merged_config['Topology'] = network_config.get('Topology', {})

        # Load agent configurations
        agents_config = {}

        for agent_name, agent_file in main_config['agents'].items():
            agent_file_path = Path(agent_file)
            if agent_file_path.is_absolute():
                agent_path = agent_file_path
            elif agent_file_path.exists():
                agent_path = agent_file_path
            else:
                agent_path = scenario_dir / agent_file

            with open(agent_path, 'r') as f:
                agent_logic = yaml.safe_load(f)

            # Check if this is a Python-based agent
            if 'python_agent' in agent_logic:
                # Python agent - pass all config through
                agents_config[agent_name] = agent_logic
            else:
                # YAML DFA agent - parse all fields
                agents_config[agent_name] = {
                    'initial_state': agent_logic.get('initial_state'),
                    'start_host': agent_logic.get('start_host', 0),
                    'states': agent_logic.get('states', []),
                    'transitions': agent_logic.get('transitions', {})
                }

                if 'reactive_transitions' in agent_logic:
                    agents_config[agent_name]['reactive_transitions'] = agent_logic['reactive_transitions']

        merged_config['Agents'] = agents_config

        # Handle monitors reference
        if 'monitors' in main_config:
            merged_config['monitors'] = main_config['monitors']

        return merged_config, scenario_path
    else:
        # Monolithic format
        return main_config, scenario_path


class ModularCage0Sim:
    """BabyCyborg simulation environment."""

    def __init__(self, scenario_path: str, max_steps: int = 20, agent_overrides: Dict[str, str] = None):
        """
        Initialize the simulation environment.

        Args:
            scenario_path: Path to the main scenario YAML file
            max_steps: Maximum number of simulation steps
            agent_overrides: Optional dict mapping agent names to agent file paths
        """
        # Load scenario and get resolved path
        self.scenario_config, resolved_scenario_path = load_modular_scenario(scenario_path, agent_overrides)

        # Initialize referee if monitors are specified
        self.referee = None
        monitors_path = self.scenario_config.get('monitors')

        if monitors_path:
            scenario_dir = resolved_scenario_path.parent
            full_monitors_path = str(scenario_dir / monitors_path)
            self.referee = Referee(full_monitors_path)

        # Initialize engine and reward calculator
        self.engine = Environment(self.scenario_config, self.referee)
        self.reward_calculator = RewardCalculator(self.scenario_config)

        # Simulation state
        self.max_steps = max_steps
        self._t = 0
        self._current_agent = 'Blue'  # Blue always acts first
        self._trace: List[Dict[str, Any]] = []
        self._episode = 0

        # Legacy compatibility properties
        self.num_hosts = self.engine.num_hosts
        self.host_names = self.engine.host_names
        self._agents = self.scenario_config['Agents']

        # YAML-based agent instances
        self.yaml_agents: Dict[str, Any] = {}

    def reset(self) -> List[str]:
        """Reset environment to initial state."""
        self.engine.reset()
        self.reward_calculator.reset()
        if self.referee:
            self.referee.reset()
        self._t = 0
        self._current_agent = 'Blue'  # Blue always acts first
        self._trace = []
        self._episode += 1
        return self.get_full_state_vector()

    def step(self, action: str, host: int, opponent_action: str = None, opponent_host: int = None) -> Dict[str, Any]:
        """Execute one simulation step: handles both agents' actions in one step."""
        assert 0 <= host < self.num_hosts, f"bad host index: {host}"

        initial_agent = self._current_agent

        # Execute current agent's action
        result = self.engine.execute_action(self._current_agent, action, host)
        reward = self.reward_calculator.calculate_reward(result)

        # Record reward and trace
        self.reward_calculator.record_reward(
            self._current_agent, action, host, reward, self._t,
            {'success': result.success, 'message': result.message}
        )

        # Create detailed trace entry for current agent
        current_agent_trace = {
            'episode': self._episode,
            'step': self._t + 1,
            'action': action,
            'agent': self._current_agent,
            'hostname': self.engine.host_names[host],
            'ip_address': self.engine.get_host_ip_address(host),
            'success': 'TRUE' if result.success else 'FALSE'
        }

        # Switch to opponent
        opponent_agent = 'Blue' if self._current_agent == 'Red' else 'Red'
        self._current_agent = opponent_agent

        # Execute opponent action
        if opponent_action is not None and opponent_host is not None:
            assert 0 <= opponent_host < self.num_hosts, f"bad opponent host index: {opponent_host}"
            opp_result = self.engine.execute_action(opponent_agent, opponent_action, opponent_host)
            opp_reward = self.reward_calculator.calculate_reward(opp_result)
            opp_success = opp_result.success
        else:
            opponent_action = 'Sleep'
            opponent_host = 0
            opp_reward = 0.0
            opp_success = True

        # Record opponent reward and trace
        self.reward_calculator.record_reward(
            opponent_agent, opponent_action, opponent_host, opp_reward, self._t,
            {'success': opp_success, 'message': 'Default action'}
        )

        # Create detailed trace entry for opponent
        opponent_trace = {
            'episode': self._episode,
            'step': self._t + 1,
            'action': opponent_action,
            'agent': opponent_agent,
            'hostname': self.engine.host_names[opponent_host],
            'ip_address': self.engine.get_host_ip_address(opponent_host),
            'success': 'TRUE' if opp_success else 'FALSE'
        }

        # Add both actions to trace in canonical order (Blue first, Red second)
        if initial_agent == 'Blue':
            self._trace.append(current_agent_trace)
            self._trace.append(opponent_trace)
        else:
            self._trace.append(opponent_trace)
            self._trace.append(current_agent_trace)

        # Advance time
        self._t += 1
        done = self._t >= self.max_steps

        # Blue always acts first in every step (fixed order, no alternating)
        self._current_agent = 'Blue'

        return {
            'state_vector': self.get_full_state_vector(),
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
        for trace_entry in reversed(self._trace):
            if trace_entry['agent'] == agent:
                return trace_entry.copy()

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
        self.yaml_agents = create_agents_from_yaml(self.scenario_config, self.engine)
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
            if not self.yaml_agents:
                self.create_yaml_agents()
        return self.yaml_agents.get(agent_name)

    def get_agent_states(self) -> Dict[str, str]:
        """
        Get current states of all agents.

        Returns:
            Dictionary mapping agent names to their current states
        """
        return {name: self.engine.get_agent_state(name) for name in self.engine.agent_names}

    def get_monitor_states(self) -> Dict[str, str]:
        """
        Get current states of all monitors.

        Returns:
            Dictionary mapping monitor names to their current states
        """
        if not self.referee or not self.referee.monitors:
            return {}
        return {monitor.name: monitor.get_state() for monitor in self.referee.monitors}

    def get_full_state_vector(self) -> List[str]:
        """
        Get complete state vector: [host_states..., agent_states..., monitor_states...].

        Returns:
            Complete state vector including hosts, agents, and monitors
        """
        state_vector = self.engine.get_state_vector()

        # Append monitor states in consistent order
        if self.referee and self.referee.monitors:
            sorted_monitors = sorted(self.referee.monitors, key=lambda m: m.name)
            for monitor in sorted_monitors:
                state_vector.append(monitor.get_state())

        return state_vector

    def auto_step(self) -> Dict[str, Any]:
        """
        Execute one simulation step using YAML-generated agents.

        For Python-based agents with update_progress(), this method
        calls the update after action execution to maintain observation-driven state.

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

        # Parse action strings
        current_action_full = current_action_dict['action']
        current_parts = current_action_full.split('_')
        current_action_name = '_'.join(current_parts[1:-1])
        current_host = int(current_parts[-1])

        opponent_action_full = opponent_action_dict['action']
        opponent_parts = opponent_action_full.split('_')
        opponent_action_name = '_'.join(opponent_parts[1:-1])
        opponent_host = int(opponent_parts[-1])

        # Execute the step
        result = self.step(
            action=current_action_name,
            host=current_host,
            opponent_action=opponent_action_name,
            opponent_host=opponent_host
        )

        # Update Python agents with observation (for observation-driven agents)
        # Blue acts first, then Red
        blue_success = result['last_actions']['Blue']['action'] != 'Sleep'
        red_info = result['last_actions']['Red']

        # Get Red action result from trace
        red_action_info = self.get_last_action('Red')
        if red_action_info:
            red_success = red_action_info['success'] == 'TRUE'
            red_agent = self.get_yaml_agent('Red')
            if hasattr(red_agent, 'update_progress'):
                red_agent.update_progress(
                    host_id=opponent_host if current_agent_name == 'Blue' else current_host,
                    action=opponent_action_name if current_agent_name == 'Blue' else current_action_name,
                    success=red_success
                )

        return result
