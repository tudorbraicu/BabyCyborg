"""
Cage0 Agents Package.

This package contains various agent implementations for the Cage0 simulator.
"""

from .base_agent import BaseAgent
from .sleep_agent import SleepAgent
from .random_red_agent import RandomRedAgent
from .killchain_red_agent import KillchainRedAgent
from .reactive_blue_agent import ReactiveBlueAgent
from .proactive_blue_agent import ProactiveBlueAgent

# Agent registry for easy access
AGENTS = {
    'sleep': SleepAgent,
    'random_red': RandomRedAgent,
    'killchain_red': KillchainRedAgent,
    'reactive_blue': ReactiveBlueAgent,
    'proactive_blue': ProactiveBlueAgent,
}


def create_agent(agent_type: str, **kwargs):
    """Create an agent by type name."""
    if agent_type not in AGENTS:
        raise ValueError(f"Unknown agent type: {agent_type}. Available: {list(AGENTS.keys())}")

    return AGENTS[agent_type](**kwargs)


__all__ = [
    'BaseAgent',
    'SleepAgent',
    'RandomRedAgent',
    'KillchainRedAgent',
    'ReactiveBlueAgent',
    'ProactiveBlueAgent',
    'AGENTS',
    'create_agent'
]