"""
HeuristicChainRedOneHost - Simple kill-chain Red agent for one host only.

Policy:
- 70%: Take next action in kill chain (DRS → DNS → ERS → PE → Impact)
- 30%: Random action on the host
"""
import random
from typing import Dict, Any
from .base_agent import BaseAgent


# Kill chain order
KILL_CHAIN = [
    'DiscoverRemoteSystems',
    'DiscoverNetworkServices',
    'ExploitRemoteService',
    'PrivilegeEscalate',
    'Impact'
]

# All valid Red actions
ALL_RED_ACTIONS = [
    'DiscoverRemoteSystems',
    'DiscoverNetworkServices',
    'ExploitRemoteService',
    'PrivilegeEscalate',
    'Impact'
]


class HeuristicChainRedOneHostAgent(BaseAgent):
    """
    Simple heuristic Red agent that follows kill chain on Host_0.

    - 70% probability: Next action in kill chain
    - 30% probability: Random action
    """

    def __init__(self, name: str = "Red", chain_probability: float = 0.7):
        """
        Initialize the agent.

        Args:
            name: Agent name (default "Red")
            chain_probability: Probability of following chain (default 0.7)
        """
        super().__init__(name)
        self.chain_probability = chain_probability
        self.host_id = 0  # Always Host_0

        # Track progress: -1 = not started, 0-4 = index in KILL_CHAIN
        self.progress = -1

    def reset(self):
        """Reset agent state for a new episode."""
        self.progress = -1

    def _get_next_chain_action(self) -> str:
        """Get the next action in the kill chain."""
        next_idx = self.progress + 1
        if next_idx < len(KILL_CHAIN):
            return KILL_CHAIN[next_idx]
        # After completing chain, restart from DRS
        return KILL_CHAIN[0]

    def _get_random_action(self) -> str:
        """Get a random valid Red action."""
        return random.choice(ALL_RED_ACTIONS)

    def get_action(self, current_step: int) -> Dict[str, Any]:
        """
        Get the next action based on heuristic policy.

        70% chain, 30% random.

        Args:
            current_step: Current step number (unused)

        Returns:
            Dictionary with 'action' key in format "Red_ActionName_0"
        """
        if random.random() < self.chain_probability:
            # 70%: Follow kill chain
            action = self._get_next_chain_action()
        else:
            # 30%: Random action
            action = self._get_random_action()

        return {'action': f'{self.name}_{action}_{self.host_id}'}

    def update_progress(self, host_id: int, action: str, success: bool):
        """
        Update internal state based on action observation.

        Args:
            host_id: Host the action was performed on (should be 0)
            action: The action that was performed
            success: Whether the action succeeded
        """
        if host_id != self.host_id:
            return  # Ignore actions on other hosts

        if not success:
            # Action failed - Blue may have removed, reset progress
            if action in ['ExploitRemoteService', 'PrivilegeEscalate', 'Impact']:
                self.progress = 0  # Restart from DNS (DRS still valid)
            return

        # Advance progress if this is the next action in chain
        expected_next = self.progress + 1
        if expected_next < len(KILL_CHAIN) and action == KILL_CHAIN[expected_next]:
            self.progress = expected_next
        # After Impact, reset to allow another chain
        elif action == 'Impact' and self.progress == len(KILL_CHAIN) - 1:
            self.progress = -1  # Restart chain

    def __repr__(self):
        return f"HeuristicChainRedOneHostAgent(progress={self.progress})"


def create_heuristic_chain_red_one_host(chain_probability: float = 0.7) -> HeuristicChainRedOneHostAgent:
    """
    Factory function to create agent.

    Args:
        chain_probability: Probability of following chain (default 0.7)

    Returns:
        Configured HeuristicChainRedOneHostAgent instance
    """
    return HeuristicChainRedOneHostAgent(name="Red", chain_probability=chain_probability)
