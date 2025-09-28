"""
RewardCalculator - Handles reward calculation and tracking.

Simplified version that focuses on essential functionality.
"""
from typing import Dict, Any


class RewardCalculator:
    """Simple reward calculator and tracker."""

    def __init__(self, scenario_config: Dict[str, Any]):
        """Initialize reward calculator with scenario configuration."""
        self.scenario_config = scenario_config
        self.total_rewards: Dict[str, float] = {'Red': 0.0, 'Blue': 0.0}

    def record_reward(self, agent: str, action: str, host_id: int, reward: float, step: int, context: Dict[str, Any] = None):
        """Record a reward for an agent."""
        self.total_rewards[agent] += reward

    def get_total_reward(self, agent: str = None) -> float:
        """Get total reward for an agent or all agents."""
        if agent is None:
            return sum(self.total_rewards.values())
        return self.total_rewards.get(agent, 0.0)

    def get_reward_summary(self) -> Dict[str, Any]:
        """Get basic reward summary."""
        return {
            'total_rewards': self.total_rewards.copy()
        }

    def reset(self):
        """Reset reward tracking for a new simulation."""
        self.total_rewards = {'Red': 0.0, 'Blue': 0.0}