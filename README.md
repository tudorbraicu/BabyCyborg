# BabyCyborg

A modular, YAML-driven cybersecurity simulation environment for studying adversarial agent interactions through deterministic finite automata (DFA).

## Overview

BabyCyborg provides a clean, extensible framework for modeling Red Team (attacker) vs Blue Team (defender) scenarios where:
- **Agents** follow explicit DFA-based strategies defined in YAML
- **Hosts** transition through security states (secure → discovered → exploited → compromised)
- **Actions** have deterministic effects on host and agent states
- **Reactive transitions** allow agents to respond to environment changes

## Features

### ✨ Core Capabilities

- **YAML-Driven Agent DFAs**: Define complete agent behavior in configuration files
- **Dual-Layer State Management**: Separate DFAs for agents and hosts
- **Reactive Transitions**: Environment-triggered state changes (e.g., Blue responds to host compromise)
- **Conditional Actions**: State-dependent action effects (e.g., Remove works differently on secure vs. compromised hosts)
- **Modular Architecture**: Clean separation between state management, action execution, and reward calculation
- **Zero Hardcoded Logic**: All agent behavior is YAML-configurable

## Quick Start

### Run a Simulation

```bash
python scripts/eval_cage0.py --scenario scenarios/explicit_dfa.yaml --yaml-agents --max-steps 20
```

**Verbose output:**
```bash
python scripts/eval_cage0.py --scenario scenarios/explicit_dfa.yaml --yaml-agents --max-steps 20 --verbose
```

### Example Output

```
Step 1: Red[s2]→DiscoverNetworkServices(h0) | Blue[b2]→NoOp(h0) | R:0/0 | Hosts:['q1', 'q0', 'q0', 'q0']
Step 2: Red[s3]→ExploitRemoteService(h0) | Blue[b5]→NoOp(h1) | R:1/0 | Hosts:['q2', 'q0', 'q0', 'q0']
Step 3: Red[s4]→PrivilegeEscalate(h0) | Blue[b1]→Remove(h0) | R:5/-1 | Hosts:['q1', 'q0', 'q0', 'q0']
...
Final rewards: {'Red': 6.0, 'Blue': -1.0}
```

## Architecture

### Component Overview

```
┌─────────────────────────────────────────┐
│         ModularCage0Sim                 │
│  • auto_step() - automatic execution    │
│  • step() - manual control              │
└────────┬────────────────────────────────┘
         │
    ┌────┴────┬───────────┬─────────────┐
    ▼         ▼           ▼             ▼
StateManager  ActionExecutor  RewardCalc  YAMLAgents
  (state)     (execution)     (tracking)  (DFA logic)
```

### Key Files

- **`cage0/modular_simulator.py`** - Main simulation orchestrator
- **`cage0/core/state_manager.py`** - Centralized state management
- **`cage0/core/action_executor.py`** - Action validation and execution
- **`cage0/agents/agent_generator.py`** - YAML → Agent class generator
- **`scenarios/explicit_dfa.yaml`** - Example scenario configuration
- **`docs/YAML_SCHEMA.md`** - Complete YAML specification

## YAML Configuration

### Minimal Example

```yaml
Agents:
  Red:
    initial_state: s1
    states: [s1, s2, s3]
    transitions:
      discover:
        action: "DiscoverNetworkServices"
        target_host: 0
        from_state: s1
        on_success: s2
        on_failure: s1
    actions:
      DiscoverNetworkServices:
        from_state: q0
        to_state: q1
        reward: 0

States: [q0, q1, q2, q3]
Hosts:
  Host_0:
    initial_state: q0
Topology:
  type: star
  num_hosts: 1
  hosts: [Host_0]
```

See [docs/YAML_SCHEMA.md](docs/YAML_SCHEMA.md) for complete documentation.

## Project Structure

```
BabyCyborg/
├── cage0/                      # Core simulation framework
│   ├── agents/                 # Agent generation and base classes
│   │   ├── agent_generator.py  # YAML → Agent class
│   │   └── base_agent.py       # Abstract agent interface
│   ├── core/                   # Core simulation components
│   │   ├── state_manager.py    # State tracking and transitions
│   │   ├── action_executor.py  # Action execution engine
│   │   └── reward_calculator.py # Reward tracking
│   └── modular_simulator.py    # Main simulator class
├── scenarios/                  # YAML scenario definitions
│   └── explicit_dfa.yaml       # Example: Red killchain vs Blue monitoring
├── scripts/                    # Command-line interfaces
│   └── eval_cage0.py           # Main CLI for running simulations
└── docs/                       # Documentation
    └── YAML_SCHEMA.md          # Complete YAML specification
```

## Usage Examples

### Python API

```python
from cage0.modular_simulator import ModularCage0Sim

# Initialize simulator
sim = ModularCage0Sim('scenarios/explicit_dfa.yaml', max_steps=20)
sim.reset()

# Run simulation
for step in range(20):
    result = sim.auto_step()
    if result['done']:
        break

# Get final summary
print(f"Final rewards: {sim.get_reward_summary()}")
print(f"Final states: {sim.get_agent_states()}")
```

### Command Line

```bash
python scripts/eval_cage0.py \
  --scenario scenarios/explicit_dfa.yaml \
  --yaml-agents \
  --max-steps 20 \
  --verbose
```

## Design Philosophy

### Why DFAs?

- **Determinism**: Same YAML always produces same results
- **Explainability**: Agent decisions are fully traceable
- **Simplicity**: Easy to understand and debug
- **Research Value**: Provides rigorous baselines for comparing learned policies

### StateManager as Single Source of Truth

All state (agent DFAs + host DFAs) lives in `StateManager`. Agents are **stateless query interfaces** that:
1. Read current state from StateManager
2. Return actions based on YAML transitions
3. StateManager updates state based on action results

This prevents state synchronization bugs and makes the system deterministic.

## License

MIT License
