"""
HeuristicChainRedMultiHost - Systematic kill-chain Red agent for multiple hosts.

Policy:
- 80%: Pick target host and take next action in chain (DRS → DNS → ERS → PE → Impact)
- 10%: Random valid action on the same host
- 10%: Hop to a different host
"""
import random
from typing import Dict, Any, List, Optional
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


class HeuristicChainRedMultiHostAgent(BaseAgent):
    """
    ProgressiveChainRed++ agent that systematically progresses through
    the kill chain with controlled noise.

    This agent is observation-driven: it proposes actions but only updates
    its internal state based on success observations (partial observability).
    """

    def __init__(self, name: str = "Red", num_hosts: int = 2, start_host: int = None,
                 prob_chain: float = 0.80, prob_random: float = 0.10, prob_switch: float = 0.10):
        """
        Initialize the agent.

        Args:
            name: Agent name (default "Red")
            num_hosts: Number of hosts in the network (default 2)
            start_host: The host Red starts on (default None = random)
            prob_chain: Probability of following kill chain (default 0.80)
            prob_random: Probability of random action on same host (default 0.10)
            prob_switch: Probability of switching to different host (default 0.10)
        """
        super().__init__(name)
        self.num_hosts = num_hosts
        # Configurable probabilities
        self.prob_chain = prob_chain
        self.prob_random = prob_random
        self.prob_switch = prob_switch
        # Random start host if not specified
        self.start_host = start_host if start_host is not None else random.randint(0, num_hosts - 1)

        # Track progress per host: -1 = not started, 0-4 = index in KILL_CHAIN, 5 = done
        # Only tracks hosts we've discovered
        self.host_progress: Dict[int, int] = {}

        # Discovered hosts - Red only knows about hosts it has discovered
        # Starts with the host Red spawns on
        self.discovered_hosts: set = set()

        # Current target host
        self.current_target: int = self.start_host

        # Initialize
        self._initialize()

    def _initialize(self):
        """Initialize agent state."""
        self.discovered_hosts = {self.start_host}
        self.host_progress = {self.start_host: -1}
        self.current_target = self.start_host

    def reset(self):
        """Reset agent state for a new episode with random start host."""
        self.start_host = random.randint(0, self.num_hosts - 1)
        self._initialize()

    def _get_any_incomplete_host(self) -> Optional[int]:
        """Get any discovered host that hasn't completed the kill chain."""
        incomplete = [h for h in self.discovered_hosts
                      if self.host_progress.get(h, -1) < len(KILL_CHAIN)]
        return random.choice(incomplete) if incomplete else None

    def _get_next_chain_action(self, host_id: int) -> str:
        """Get the next action in the kill chain for a host."""
        progress = self.host_progress.get(host_id, -1)
        next_idx = progress + 1
        if next_idx < len(KILL_CHAIN):
            return KILL_CHAIN[next_idx]
        # Progress=4 means Impact done once, need second Impact to complete (progress=5)
        if progress == len(KILL_CHAIN) - 1:
            return 'Impact'
        # Host is truly done (progress=5), restart chain from DNS
        return 'DiscoverNetworkServices'

    def _get_random_action(self) -> str:
        """Get a random valid Red action."""
        return random.choice(ALL_RED_ACTIONS)

    def _get_other_host(self, current_host: int) -> int:
        """Get a random different discovered host (for switching)."""
        other_hosts = [h for h in self.discovered_hosts if h != current_host]
        return random.choice(list(other_hosts)) if other_hosts else current_host

    def get_action(self, current_step: int) -> Dict[str, Any]:
        """
        Get the next action based on the progressive chain policy.

        Policy breakdown:
        - 80%: Continue kill chain on current target (stay on same host)
        - 10%: Random action on same host
        - 10%: Switch to random different host and STAY there (sticky switch)

        This method is observation-driven: it proposes actions but does NOT
        update internal state. State updates happen in update_progress()
        based on actual success observations.

        Args:
            current_step: Current step number (unused but required by interface)

        Returns:
            Dictionary with 'action' key in format "Red_ActionName_HostId"
        """
        # If current target is complete, pick any incomplete host
        if self.host_progress.get(self.current_target, -1) >= len(KILL_CHAIN):
            new_target = self._get_any_incomplete_host()
            if new_target is not None:
                self.current_target = new_target

        target_host = self.current_target

        # Roll the dice based on configured probabilities
        roll = random.random()

        if roll < self.prob_chain:
            # Follow kill chain on current target
            action = self._get_next_chain_action(target_host)
            host = target_host

        elif roll < self.prob_chain + self.prob_random:
            # Random action on same host (noise)
            action = self._get_random_action()
            host = target_host

        else:
            # STICKY switch to different discovered host
            new_host = self._get_other_host(target_host)
            self.current_target = new_host  # Stay on new host!
            action = self._get_next_chain_action(new_host)
            host = new_host

        return {'action': f'{self.name}_{action}_{host}'}

    def update_progress(self, host_id: int, action: str, success: bool):
        """
        Update internal state based on action observation (success/failure).

        This is the observation-driven update that maintains partial observability.
        Called after each action to update:
        - Kill chain progress (only on success of expected next action)
        - Discovered hosts (on successful DiscoverRemoteSystems)

        Args:
            host_id: Host the action was performed on
            action: The action that was performed
            success: Whether the action succeeded
        """
        # Handle host discovery - DRS reveals new hosts
        if action == 'DiscoverRemoteSystems' and success:
            # In BabyCyborg, successful DRS on a host reveals neighboring hosts
            # For simplicity, assume it reveals all hosts (or specific logic can be added)
            # For now, we discover all hosts on first successful DRS
            for h in range(self.num_hosts):
                if h not in self.discovered_hosts:
                    self.discovered_hosts.add(h)
                    self.host_progress[h] = -1  # Initialize progress for new host

        if not success:
            # Action failed - host state may have been reset by Blue's Remove
            # Remove resets host to q0 (discovered but services not scanned)
            # So we reset progress to 0 (DRS done) to restart from DNS
            if action in ['ExploitRemoteService', 'PrivilegeEscalate', 'Impact']:
                if host_id in self.host_progress:
                    self.host_progress[host_id] = 0  # Restart from DNS
            return

        # Ensure host is in our tracking
        if host_id not in self.host_progress:
            self.host_progress[host_id] = -1

        current_progress = self.host_progress[host_id]
        expected_next = current_progress + 1

        # Advance progress if this action is the next one in the chain
        if expected_next < len(KILL_CHAIN) and action == KILL_CHAIN[expected_next]:
            self.host_progress[host_id] = expected_next
        # Mark host as fully complete after Impact
        elif action == 'Impact' and current_progress == len(KILL_CHAIN) - 1:
            self.host_progress[host_id] = len(KILL_CHAIN)

    def __repr__(self):
        progress_str = ', '.join(f'H{h}:{p}' for h, p in self.host_progress.items())
        return f"HeuristicChainRedMultiHostAgent(target={self.current_target}, progress=[{progress_str}])"


def create_progressive_chain_red(num_hosts: int = 2, prob_chain: float = 0.80,
                                  prob_random: float = 0.10, prob_switch: float = 0.10) -> HeuristicChainRedMultiHostAgent:
    """
    Factory function to create a ProgressiveChainRed++ agent.

    Args:
        num_hosts: Number of hosts in the network
        prob_chain: Probability of following kill chain (default 0.80)
        prob_random: Probability of random action on same host (default 0.10)
        prob_switch: Probability of switching to different host (default 0.10)

    Returns:
        Configured HeuristicChainRedMultiHostAgent instance
    """
    return HeuristicChainRedMultiHostAgent(name="Red", num_hosts=num_hosts,
                                    prob_chain=prob_chain, prob_random=prob_random,
                                    prob_switch=prob_switch)
