"""
BabyCyborg - A modular cybersecurity simulation framework.

Main components:
- simulator: Main simulation interface (ModularCage0Sim)
- environment: Environment state management
- monitors: Monitor automata and referee logic
- reward_calculator: Reward computation
- agents: Agent generation and logic
"""

from .simulator import ModularCage0Sim

__all__ = ['ModularCage0Sim']
