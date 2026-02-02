"""
Shared pytest fixtures for BabyCyborg tests.
"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from cage0.environment import Environment
from cage0.simulator import ModularCage0Sim
from cage0.monitors import Monitor, Referee
from cage0.actions.base import ActionResult


@pytest.fixture
def basic_scenario_config():
    """Basic scenario configuration for testing."""
    return {
        'Topology': {
            'num_hosts': 4,
            'hosts': ['Host_0', 'Host_1', 'Host_2', 'Host_3']
        },
        'Hosts': {
            'Host_0': {'initial_state': 'q0', 'ip_address': '10.0.0.1'},
            'Host_1': {'initial_state': 'q0', 'ip_address': '10.0.0.2'},
            'Host_2': {'initial_state': 'q0', 'ip_address': '10.0.0.3'},
            'Host_3': {'initial_state': 'q0', 'ip_address': '10.0.0.4'},
        },
        'Agents': {
            'Red': {'initial_state': 'r0', 'start_host': 0},
            'Blue': {'initial_state': 'b0', 'start_host': 0}
        }
    }


@pytest.fixture
def environment(basic_scenario_config):
    """Create a basic environment for testing."""
    env = Environment(basic_scenario_config)
    env.reset()
    return env


@pytest.fixture
def simple_monitor_config():
    """Simple monitor configuration for testing."""
    return {
        'name': 'TestMonitor',
        'initial_state': 'm0',
        'states': ['m0', 'm1', 'm0_recv', 'm0_emit'],
        'transitions': [
            # Receive action
            {'from_state': 'm0', 'transition': '?Red_Attack_0', 'to_state': 'm0_recv'},
            # Emit success
            {'from_state': 'm0_recv', 'transition': '!success', 'to_state': 'm0_emit'},
            # ACK
            {'from_state': 'm0_emit', 'transition': '?Referee_Result_1', 'to_state': 'm1'},
            {'from_state': 'm0_emit', 'transition': '?Referee_Result_0', 'to_state': 'm0'},
        ]
    }


@pytest.fixture
def blocking_monitor_config():
    """Monitor that blocks certain actions."""
    return {
        'name': 'BlockingMonitor',
        'initial_state': 'm0',
        'states': ['m0', 'm0_recv', 'm0_emit'],
        'transitions': [
            # Receive blocked action
            {'from_state': 'm0', 'transition': '?Red_BadAction_0', 'to_state': 'm0_recv'},
            # Emit failure
            {'from_state': 'm0_recv', 'transition': '!failure', 'to_state': 'm0_emit'},
            # ACK (stays in m0)
            {'from_state': 'm0_emit', 'transition': '?Referee_Result_0', 'to_state': 'm0'},
        ]
    }


@pytest.fixture
def network_validity_h0_config():
    """Simplified NetworkValidity monitor for Host_0."""
    return {
        'name': 'NetworkValidity_H0',
        'initial_state': 'q0',
        'states': [
            'q0', 'q1', 'q2', 'q3',
            'q0_dns_recv', 'q0_dns_emit',
            'q1_ers_recv', 'q1_ers_emit',
            'q2_pe_recv', 'q2_pe_emit',
            'q3_imp_recv', 'q3_imp_emit',
            'q0_fail_recv', 'q0_fail_emit',
            'q1_fail_recv', 'q1_fail_emit',
            'q2_fail_recv', 'q2_fail_emit',
        ],
        'transitions': [
            # q0: Only DiscoverNetworkServices allowed
            {'from_state': 'q0', 'transition': '?Red_DiscoverNetworkServices_0', 'to_state': 'q0_dns_recv'},
            {'from_state': 'q0_dns_recv', 'transition': '!success', 'to_state': 'q0_dns_emit'},
            {'from_state': 'q0_dns_emit', 'transition': '?Referee_Result_1', 'to_state': 'q1'},
            {'from_state': 'q0_dns_emit', 'transition': '?Referee_Result_0', 'to_state': 'q0'},

            # q0: Other Red actions fail
            {'from_state': 'q0', 'transition': '?Red_ExploitRemoteService_0', 'to_state': 'q0_fail_recv'},
            {'from_state': 'q0', 'transition': '?Red_PrivilegeEscalate_0', 'to_state': 'q0_fail_recv'},
            {'from_state': 'q0', 'transition': '?Red_Impact_0', 'to_state': 'q0_fail_recv'},
            {'from_state': 'q0_fail_recv', 'transition': '!failure', 'to_state': 'q0_fail_emit'},
            {'from_state': 'q0_fail_emit', 'transition': '?Referee_Result_0', 'to_state': 'q0'},

            # q1: ExploitRemoteService allowed
            {'from_state': 'q1', 'transition': '?Red_ExploitRemoteService_0', 'to_state': 'q1_ers_recv'},
            {'from_state': 'q1_ers_recv', 'transition': '!success', 'to_state': 'q1_ers_emit'},
            {'from_state': 'q1_ers_emit', 'transition': '?Referee_Result_1', 'to_state': 'q2'},
            {'from_state': 'q1_ers_emit', 'transition': '?Referee_Result_0', 'to_state': 'q1'},

            # q1: Other actions fail
            {'from_state': 'q1', 'transition': '?Red_PrivilegeEscalate_0', 'to_state': 'q1_fail_recv'},
            {'from_state': 'q1', 'transition': '?Red_Impact_0', 'to_state': 'q1_fail_recv'},
            {'from_state': 'q1_fail_recv', 'transition': '!failure', 'to_state': 'q1_fail_emit'},
            {'from_state': 'q1_fail_emit', 'transition': '?Referee_Result_0', 'to_state': 'q1'},

            # q2: PrivilegeEscalate allowed
            {'from_state': 'q2', 'transition': '?Red_PrivilegeEscalate_0', 'to_state': 'q2_pe_recv'},
            {'from_state': 'q2_pe_recv', 'transition': '!success', 'to_state': 'q2_pe_emit'},
            {'from_state': 'q2_pe_emit', 'transition': '?Referee_Result_1', 'to_state': 'q3'},
            {'from_state': 'q2_pe_emit', 'transition': '?Referee_Result_0', 'to_state': 'q2'},

            # q2: Impact fails
            {'from_state': 'q2', 'transition': '?Red_Impact_0', 'to_state': 'q2_fail_recv'},
            {'from_state': 'q2_fail_recv', 'transition': '!failure', 'to_state': 'q2_fail_emit'},
            {'from_state': 'q2_fail_emit', 'transition': '?Referee_Result_0', 'to_state': 'q2'},

            # q3: Impact allowed
            {'from_state': 'q3', 'transition': '?Red_Impact_0', 'to_state': 'q3_imp_recv'},
            {'from_state': 'q3_imp_recv', 'transition': '!success', 'to_state': 'q3_imp_emit'},
            {'from_state': 'q3_imp_emit', 'transition': '?Referee_Result_1', 'to_state': 'q3'},
            {'from_state': 'q3_imp_emit', 'transition': '?Referee_Result_0', 'to_state': 'q3'},
        ]
    }
