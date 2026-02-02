"""
ActionSpace - Tracks what agents know and can do.

Inspired by CybORG's ActionSpace, this tracks an agent's knowledge of the network
as distinct state. An agent can only perform actions on hosts it has discovered.
"""
from typing import Dict, Set, List


class ActionSpace:
    """
    Tracks an agent's knowledge of the network.

    In cybersecurity simulations, agents can only act on resources they've discovered.
    This class maintains the "fog of war" - what hosts an agent knows about.

    Similar to CybORG/Shared/ActionSpace.py but simplified for BabyCyborg's needs.
    """

    def __init__(self, agent_name: str, num_hosts: int, allowed_actions: Dict):
        """
        Initialize ActionSpace for an agent.

        Args:
            agent_name: Name of the agent (e.g., 'Red', 'Blue')
            num_hosts: Total number of hosts in the network
            allowed_actions: Dictionary of actions this agent can perform
        """
        self.agent_name = agent_name
        self.num_hosts = num_hosts
        self.allowed_actions = allowed_actions

        # Track discovered hosts (initially empty set)
        self.discovered_hosts: Set[int] = set()

    def discover_host(self, host_id: int) -> None:
        """
        Mark a host as discovered.

        Args:
            host_id: Host to add to discovered set
        """
        if 0 <= host_id < self.num_hosts:
            self.discovered_hosts.add(host_id)

    def discover_all_hosts(self) -> None:
        """Mark all hosts as discovered (for broadcast discovery actions)."""
        self.discovered_hosts = set(range(self.num_hosts))

    def is_host_discovered(self, host_id: int) -> bool:
        """
        Check if agent has discovered a host.

        Args:
            host_id: Host to check

        Returns:
            True if host is discovered, False otherwise
        """
        return host_id in self.discovered_hosts

    def get_discovered_hosts(self) -> List[int]:
        """
        Get list of all discovered hosts.

        Returns:
            Sorted list of discovered host IDs
        """
        return sorted(list(self.discovered_hosts))

    def can_perform_action(self, action_name: str, host_id: int) -> tuple[bool, str]:
        """
        Check if agent can perform an action on a host.

        Note: This now works with action classes instead of action dicts.
        Broadcast actions are handled in environment.py.

        Args:
            action_name: Name of action to perform
            host_id: Target host

        Returns:
            Tuple of (can_perform, reason)
        """
        # Check if action exists for this agent
        if action_name not in self.allowed_actions:
            return False, f"Action '{action_name}' not available for agent '{self.agent_name}'"

        # All actions require the host to be discovered
        # (Broadcast actions like DRS are exempted in environment.py before calling this)
        if not self.is_host_discovered(host_id):
            return False, f"Host {host_id} not discovered by agent '{self.agent_name}'"

        return True, "Action allowed"

    def get_action_space(self) -> Dict:
        """
        Get current action space in CybORG-compatible format.

        Returns dict mapping parameter types to {value: bool} where:
        - True = discovered/known
        - False = exists but not discovered

        Returns:
            Dictionary representation of action space
        """
        # Build hostname dictionary: True if discovered, False otherwise
        hostname_dict = {}
        for host_id in range(self.num_hosts):
            hostname_dict[host_id] = (host_id in self.discovered_hosts)

        # Build action dictionary
        action_dict = {}
        for action_name in self.allowed_actions.keys():
            action_dict[action_name] = True  # Actions themselves are always available

        return {
            'action': action_dict,
            'hostname': hostname_dict,
            'discovered_hosts': list(self.discovered_hosts)
        }

    def reset(self) -> None:
        """Reset action space to initial state (no discovered hosts)."""
        self.discovered_hosts = set()

    def __repr__(self) -> str:
        return (f"ActionSpace(agent='{self.agent_name}', "
                f"discovered={sorted(list(self.discovered_hosts))})")
