"""
Baby CybORG - Simple cyber simulation environment.

Everything is scenario-driven: actions, states, rewards, transitions.
Single file implementation for maximum simplicity.
"""
import yaml
from typing import List, Dict, Any


class Cage0Sim:
    """Baby CybORG simulation environment."""

    def __init__(self, scenario_path: str, max_steps: int = 20):
        """Initialize the simulation environment."""
        with open(scenario_path, 'r') as f:
            scenario = yaml.safe_load(f)

        self.num_hosts = scenario['Topology']['num_hosts']
        self.host_names = scenario['Topology']['hosts']
        self._agents = scenario['Agents']

        self.max_steps = max_steps
        self._t = 0
        self._current_agent = 'Red'
        self._hosts: List[str] = []
        self._trace: List[Dict[str, Any]] = []
        self._total_reward = 0.0

    def reset(self) -> List[str]:
        """Reset environment to initial state."""
        self._hosts = ['q0'] * self.num_hosts
        self._t = 0
        self._current_agent = 'Red'
        self._total_reward = 0.0
        self._trace = []
        return self._hosts.copy()

    def step(self, action: str, host: int, opponent_action: str = None, opponent_host: int = None) -> Dict[str, Any]:
        """Execute one simulation step: handles both agents' actions in one step."""
        assert 0 <= host < self.num_hosts, f"bad host index: {host}"

        # Store initial agent
        initial_agent = self._current_agent

        # Execute current agent's action
        prev_state = self._hosts[host]
        new_state, reward = self._apply_action(self._current_agent, prev_state, action)
        self._hosts[host] = new_state

        # Log current agent's action
        current_agent_trace = {
            'agent': self._current_agent[0],  # 'R' or 'B'
            'action': action,
            'host': host,
            'reward': reward
        }

        # Switch to opponent
        opponent_agent = 'Blue' if self._current_agent == 'Red' else 'Red'
        self._current_agent = opponent_agent

        # If opponent action is provided, execute it; otherwise get a default action
        if opponent_action is not None and opponent_host is not None:
            assert 0 <= opponent_host < self.num_hosts, f"bad opponent host index: {opponent_host}"
            opp_prev_state = self._hosts[opponent_host]
            opp_new_state, opp_reward = self._apply_action(opponent_agent, opp_prev_state, opponent_action)
            self._hosts[opponent_host] = opp_new_state
        else:
            # Default opponent action (Sleep/no-op)
            opponent_action = 'Sleep'
            opponent_host = 0  # Default to first host
            opp_reward = 0.0

        # Log opponent's action
        opponent_trace = {
            'agent': opponent_agent[0],  # 'R' or 'B'
            'action': opponent_action,
            'host': opponent_host,
            'reward': opp_reward
        }

        # Add both actions to trace (current agent first, then opponent)
        self._trace.append(current_agent_trace)
        self._trace.append(opponent_trace)

        # Update total reward (add both rewards)
        total_step_reward = reward + opp_reward
        self._total_reward += total_step_reward

        # Advance time (one step = both agents acted)
        self._t += 1
        done = self._t >= self.max_steps

        # Return to the agent that should act next (alternating from initial)
        self._current_agent = 'Blue' if initial_agent == 'Red' else 'Red'

        return {
            'state_vector': self._hosts.copy(),
            'reward': reward,  # Return primary agent's reward
            'opponent_reward': opp_reward,
            'total_step_reward': total_step_reward,
            'done': done,
            'total_reward': self._total_reward,
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
        return self._total_reward

    def get_trace(self) -> List[Dict[str, Any]]:
        """Get the simple trace: Agent, action, host, reward."""
        return self._trace.copy()

    def get_last_action(self, agent: str) -> Dict[str, Any]:
        """Get the last action taken by a specific agent."""
        agent_letter = agent[0].upper()  # 'R' or 'B'

        # Search from the end of trace to find most recent action by this agent
        for trace_entry in reversed(self._trace):
            if trace_entry['agent'] == agent_letter:
                return {
                    'action': trace_entry['action'],
                    'host': trace_entry['host'],
                    'reward': trace_entry['reward']
                }

        # Return None if no action found for this agent
        return None

    def get_last_actions(self) -> Dict[str, Dict[str, Any]]:
        """Get the last actions for both agents."""
        return {
            'Red': self.get_last_action('Red'),
            'Blue': self.get_last_action('Blue')
        }

    def _apply_action(self, agent: str, state: str, action: str) -> tuple[str, float]:
        """Apply action and return new state and reward."""
        # Get action definition from scenario
        agent_actions = self._agents.get(agent, {}).get('actions', {})
        action_def = agent_actions.get(action, {})

        if not action_def:
            return state, 0.0  # Invalid action

        from_state = action_def.get('from_state')
        to_state = action_def.get('to_state')
        reward = action_def.get('reward', 0)

        # Check if action is valid for current state
        if from_state != 'any' and from_state != state:
            return state, 0.0  # Invalid state

        # Apply transition
        if to_state == 'same':
            new_state = state
        elif to_state == 'q1' and action == 'Remove':
            # Special case for Remove: q0->q0, others->q1
            new_state = 'q0' if state == 'q0' else 'q1'
        else:
            new_state = to_state

        return new_state, reward


