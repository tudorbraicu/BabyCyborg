"""
Actions module - Concrete action classes for BabyCyborg.

Each action is implemented as a specific class with hard-coded logic,
similar to CybORG's action class hierarchy.
"""

from .base import Action, ActionResult
from .red_actions import (
    DiscoverRemoteSystems,
    DiscoverNetworkServices,
    ExploitRemoteService,
    PrivilegeEscalate,
    Impact
)
from .blue_actions import NoOp, Remove

# Action registry - maps action names to classes
RED_ACTIONS = {
    'DiscoverRemoteSystems': DiscoverRemoteSystems,
    'DiscoverNetworkServices': DiscoverNetworkServices,
    'ExploitRemoteService': ExploitRemoteService,
    'PrivilegeEscalate': PrivilegeEscalate,
    'Impact': Impact
}

BLUE_ACTIONS = {
    'NoOp': NoOp,
    'Remove': Remove
}

ALL_ACTIONS = {**RED_ACTIONS, **BLUE_ACTIONS}


__all__ = [
    'Action',
    'ActionResult',
    'DiscoverRemoteSystems',
    'DiscoverNetworkServices',
    'ExploitRemoteService',
    'PrivilegeEscalate',
    'Impact',
    'NoOp',
    'Remove',
    'RED_ACTIONS',
    'BLUE_ACTIONS',
    'ALL_ACTIONS'
]
