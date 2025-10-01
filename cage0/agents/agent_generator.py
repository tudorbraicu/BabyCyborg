"""
Agent Generator - Creates agent classes from YAML DFA specifications.

This module reads YAML files and generates concrete agent classes that implement
the DFA logic specified in the configuration.
"""
from typing import Dict, Any
from .base_agent import BaseAgent


def generate_agent_class(agent_name: str, agent_config: Dict[str, Any], state_manager) -> type:
    """
    Generate a concrete agent class from YAML configuration.

    Args:
        agent_name: Name of the agent (e.g., "Red", "Blue")
        agent_config: Agent configuration from YAML
        state_manager: Reference to StateManager

    Returns:
        A new agent class that implements the YAML-specified DFA
    """

    class GeneratedAgent(BaseAgent):
        def __init__(self, name: str = agent_name):
            super().__init__(name)
            self.state_manager = state_manager
            self.agent_config = agent_config
            self.transitions = agent_config.get('transitions', {})

            # Initialize agent to its starting state
            initial_state = agent_config.get('initial_state', 'p0')
            try:
                current = self.state_manager.get_agent_state(self.name)
            except ValueError:
                # Agent state not yet set, initialize it
                self.state_manager.set_agent_state(self.name, initial_state)

        def get_action(self, current_step: int) -> Dict[str, Any]:
            """
            Get action based on current DFA state from StateManager.

            StateManager owns the agent's DFA state. This method simply
            queries the current state and returns the corresponding action
            from the YAML transitions.

            State updates happen automatically in StateManager when
            ActionExecutor executes the action.

            Returns:
                Dictionary with 'action' and 'host' keys
            """
            current_state = self.state_manager.get_agent_state(self.name)

            # Find the transition that matches current state
            for transition_name, transition_config in self.transitions.items():
                if transition_config.get('from_state') == current_state:
                    action = transition_config.get('action')
                    target_host = transition_config.get('target_host')

                    # Check if action is hostless (explicit null or missing)
                    if action:
                        # If target_host is explicitly null, use 0 as placeholder
                        # (for hostless actions like NoOp)
                        if target_host is None:
                            # Check if this is truly a hostless action
                            action_defs = self.agent_config.get('actions', {})
                            action_def = action_defs.get(action, {})
                            if action_def.get('hostless', False):
                                target_host = 0  # Placeholder for hostless actions
                            else:
                                continue  # Missing required target_host

                        return {
                            'action': action,
                            'host': target_host
                        }

            # Fallback: return a safe default action
            return {
                'action': 'NoOp' if agent_name == 'Blue' else 'Sleep',
                'host': 0
            }

        def __repr__(self):
            try:
                current_state = self.state_manager.get_agent_state(self.name)
            except:
                current_state = 'unknown'
            return f"{agent_name}Agent(state='{current_state}')"

    # Set the class name dynamically
    GeneratedAgent.__name__ = f"{agent_name}Agent"
    GeneratedAgent.__qualname__ = f"{agent_name}Agent"

    return GeneratedAgent


def create_agents_from_yaml(scenario_config: Dict[str, Any], state_manager) -> Dict[str, BaseAgent]:
    """
    Create agent instances from YAML scenario configuration.

    Args:
        scenario_config: Complete scenario configuration
        state_manager: StateManager instance

    Returns:
        Dictionary mapping agent names to agent instances
    """
    agents = {}
    agents_config = scenario_config.get('Agents', {})

    for agent_name, agent_config in agents_config.items():
        # Generate the agent class
        agent_class = generate_agent_class(agent_name, agent_config, state_manager)

        # Create an instance
        agents[agent_name] = agent_class()

    return agents