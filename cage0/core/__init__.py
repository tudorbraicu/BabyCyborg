"""
Core components for BabyCyborg modular architecture.

This package contains the refactored components that replace the monolithic simulator:
- StateManager: Handles host state management and transitions
- ActionExecutor: Handles action execution and validation
- RewardCalculator: Handles reward calculation and tracking
"""

from .state_manager import StateManager
from .action_executor import ActionExecutor, ActionResult
from .reward_calculator import RewardCalculator

__all__ = [
    'StateManager',
    'ActionExecutor',
    'ActionResult',
    'RewardCalculator'
]