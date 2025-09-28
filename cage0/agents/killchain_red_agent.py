"""
Killchain Red Agent - Follows systematic attack progression.
"""
from typing import List, Dict, Any
from .base_agent import BaseAgent


class KillchainRedAgent(BaseAgent):
    """
    Sophisticated Red agent that follows a systematic kill chain approach.

    Attack progression:
    1. Discover services on q0 hosts (q0 -> q1)
    2. Exploit discovered services (q1 -> q2)
    3. Privilege escalate (q2 -> q3)
    4. Impact on fully compromised hosts (q3 -> q3)
    """

    def __init__(self, name: str = "KillchainRed"):
        """
        Initialize the Killchain Red Agent.

        Args:
            name: Name of the agent
        """
        super().__init__(name)
        self.target_sequence = []  # Track which hosts we're targeting

    def get_action(self, state_vector: List[str], host_states: Dict[int, str], current_step: int) -> Dict[str, Any]:
        """
        Follow kill chain progression with priority:
        1. Impact on fully compromised hosts (q3)
        2. Privilege escalate on exploited hosts (q2)
        3. Exploit services on discovered hosts (q1)
        4. Discover services on secure hosts (q0)

        Args:
            state_vector: List of host states
            host_states: Dictionary mapping host index to state
            current_step: Current step number

        Returns:
            Dictionary with strategic action and target host
        """
        # Build host state map
        host_states = {i: state for i, state in enumerate(state_vector)}

        # Priority 1: Impact on fully compromised hosts (q3)
        q3_hosts = [host for host, state in host_states.items() if state == 'q3']
        if q3_hosts:
            return {'action': 'Impact', 'host': q3_hosts[0]}

        # Priority 2: Privilege escalate on exploited hosts (q2)
        q2_hosts = [host for host, state in host_states.items() if state == 'q2']
        if q2_hosts:
            return {'action': 'PrivilegeEscalate', 'host': q2_hosts[0]}

        # Priority 3: Exploit services on discovered hosts (q1)
        q1_hosts = [host for host, state in host_states.items() if state == 'q1']
        if q1_hosts:
            return {'action': 'ExploitRemoteService', 'host': q1_hosts[0]}

        # Priority 4: Discover services on secure hosts (q0)
        q0_hosts = [host for host, state in host_states.items() if state == 'q0']
        if q0_hosts:
            return {'action': 'DiscoverNetworkServices', 'host': q0_hosts[0]}

        # Fallback: randomly pick an action if all hosts are compromised
        return {'action': 'Impact', 'host': 0}