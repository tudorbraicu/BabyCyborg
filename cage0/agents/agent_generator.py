"""
Agent Generator - Creates agent classes from YAML DFA specifications or Python modules.

Supports:
- YAML DFA agents (traditional format)
- Python-based agents (for more complex behaviors like ProgressiveChainRed++)
"""
import random
from typing import Dict, Any, Optional
from .base_agent import BaseAgent


def load_python_agent(agent_type: str, agent_name: str, num_hosts: int = 4,
                      prob_chain: float = 0.80, prob_random: float = 0.10, prob_switch: float = 0.10):
    """
    Load a Python-based agent by type name.

    Args:
        agent_type: Type of Python agent (e.g., 'progressive_chain_red')
        agent_name: Name for the agent (e.g., 'Red')
        num_hosts: Number of hosts in the network
        prob_chain: Probability of following kill chain (for progressive_chain_red)
        prob_random: Probability of random action (for progressive_chain_red)
        prob_switch: Probability of switching host (for progressive_chain_red)

    Returns:
        Instantiated Python agent
    """
    if agent_type == 'heuristic_chain_red_multi_host':
        from .red_agents.heuristic_chain_red_multi_host import HeuristicChainRedMultiHostAgent
        return HeuristicChainRedMultiHostAgent(name=agent_name, num_hosts=num_hosts,
                                               prob_chain=prob_chain, prob_random=prob_random,
                                               prob_switch=prob_switch)
    elif agent_type == 'heuristic_chain_red_one_host':
        from .red_agents.heuristic_chain_red_one_host import HeuristicChainRedOneHostAgent
        return HeuristicChainRedOneHostAgent(name=agent_name)
    elif agent_type == 'remove_host0_blue':
        from .blue_agents.remove_host0_blue import RemoveHost0BlueAgent
        return RemoveHost0BlueAgent(name=agent_name)
    else:
        raise ValueError(f"Unknown Python agent type: {agent_type}")


def generate_agent_class(agent_name: str, agent_config: Dict[str, Any], engine) -> type:
    """
    Generate a concrete agent class from YAML configuration.

    Args:
        agent_name: Name of the agent (e.g., "Red", "Blue")
        agent_config: Agent configuration from YAML
        engine: Reference to Engine

    Returns:
        A new agent class that implements the YAML-specified DFA
    """

    class GeneratedAgent(BaseAgent):
        def __init__(self, name: str = agent_name):
            super().__init__(name)
            self.engine = engine
            self.agent_config = agent_config
            self.transitions = agent_config.get('transitions', {})

            # Initialize agent to its starting state
            initial_state = agent_config.get('initial_state', 'p0')
            try:
                current = self.engine.get_agent_state(self.name)
            except ValueError:
                # Agent state not yet set, initialize it
                self.engine.set_agent_state(self.name, initial_state)

        def get_action(self, current_step: int) -> Dict[str, Any]:
            """
            Get action based on current DFA state from Engine.

            Engine owns the agent's DFA state. This method simply
            queries the current state and returns the corresponding action
            from the YAML transitions.

            If multiple send transitions exist from the current state,
            one is randomly selected.

            State updates happen automatically in Engine when
            actions are executed.

            Returns:
                Dictionary with single 'action' key containing full action string
                Format: "AgentName_ActionName_HostId" (e.g., "Red_Impact_1")
            """
            current_state = self.engine.get_agent_state(self.name)

            # Handle new list-based transitions format
            if isinstance(self.transitions, list):
                # Collect ALL send transitions (!action) from current state
                valid_actions = []
                for transition in self.transitions:
                    if transition.get('from_state') == current_state:
                        trans_label = transition.get('transition', '')
                        if trans_label.startswith('!'):
                            # This is a send transition
                            action = trans_label[1:]  # Remove ! prefix
                            valid_actions.append(action)

                # Randomly select one if multiple exist
                if valid_actions:
                    action = random.choice(valid_actions)

                    # Check if action contains "random" placeholder for host ID
                    if action.endswith('_random'):
                        # Generate random host ID
                        num_hosts = self.engine.num_hosts
                        random_host = random.randint(0, num_hosts - 1)
                        # Replace "random" with actual host ID
                        action = action.replace('_random', f'_{random_host}')

                    # Action string in format "AgentName_ActionName_HostId"
                    return {'action': action}

            # Legacy dict-based format
            else:
                # Collect ALL send transitions from current state
                valid_actions = []
                for transition_name, transition_config in self.transitions.items():
                    if transition_config.get('from_state') == current_state:
                        action = transition_config.get('action')

                        if action:
                            # Remove the "!" prefix if present (send marker)
                            if action.startswith('!'):
                                action = action[1:]
                            valid_actions.append(action)

                # Randomly select one if multiple exist
                if valid_actions:
                    action = random.choice(valid_actions)

                    # Check if action contains "random" placeholder for host ID
                    if action.endswith('_random'):
                        # Generate random host ID
                        num_hosts = self.engine.num_hosts
                        random_host = random.randint(0, num_hosts - 1)
                        # Replace "random" with actual host ID
                        action = action.replace('_random', f'_{random_host}')

                    # Action string should be in format "AgentName_ActionName_HostId"
                    return {'action': action}

            # Fallback: return a safe default action
            default_action = 'NoOp' if agent_name == 'Blue' else 'Sleep'
            return {'action': f'{agent_name}_{default_action}_0'}

        def __repr__(self):
            try:
                current_state = self.engine.get_agent_state(self.name)
            except:
                current_state = 'unknown'
            return f"{agent_name}Agent(state='{current_state}')"

    # Set the class name dynamically
    GeneratedAgent.__name__ = f"{agent_name}Agent"
    GeneratedAgent.__qualname__ = f"{agent_name}Agent"

    return GeneratedAgent


def create_agents_from_yaml(scenario_config: Dict[str, Any], engine) -> Dict[str, BaseAgent]:
    """
    Create agent instances from YAML scenario configuration.

    Supports both YAML DFA agents and Python-based agents.
    To use a Python agent, include 'python_agent: <type>' in the agent config.

    Args:
        scenario_config: Complete scenario configuration
        engine: Engine instance

    Returns:
        Dictionary mapping agent names to agent instances
    """
    agents = {}
    agents_config = scenario_config.get('Agents', {})

    for agent_name, agent_config in agents_config.items():
        # Check if this is a Python-based agent
        python_agent_type = agent_config.get('python_agent')

        if python_agent_type:
            # Load Python agent - use num_hosts from config if specified, else engine default
            agent_num_hosts = agent_config.get('num_hosts', engine.num_hosts)
            # Get probability parameters (defaults: 80% chain, 10% random, 10% switch)
            prob_chain = agent_config.get('prob_chain', 0.80)
            prob_random = agent_config.get('prob_random', 0.10)
            prob_switch = agent_config.get('prob_switch', 0.10)
            agents[agent_name] = load_python_agent(
                agent_type=python_agent_type,
                agent_name=agent_name,
                num_hosts=agent_num_hosts,
                prob_chain=prob_chain,
                prob_random=prob_random,
                prob_switch=prob_switch
            )
        else:
            # Generate YAML DFA agent class
            agent_class = generate_agent_class(agent_name, agent_config, engine)
            agents[agent_name] = agent_class()

    return agents