# BabyCyborg

A modular, YAML-driven cybersecurity simulation environment for studying adversarial agent interactions through deterministic finite automata (DFA).

## Overview

BabyCyborg is a modular cybersecurity simulation framework based on **communicating automata**. The system decomposes into independent DFAs that coordinate through message-passing:

- **Agents** (Red/Blue) follow DFA strategies defined in YAML, emitting actions and receiving verdicts
- **Hosts** transition through security states (q0 → q1 → q2 → q3)
- **Monitors** validate actions via a three-phase protocol (Receive → Emit → Decision Broadcast)
- **Network Validity Monitors** shadow host states and enforce valid state transitions

## Quick Start

### Run a Simulation

```bash
python scripts/eval_cage0.py --scenario yaml_files/config/four_host_heuristic_red_random_blue.yaml --max-steps 20
```

### Generate Training Traces

```bash
python scripts/generate_traces.py \
    --scenario yaml_files/config/four_host_heuristic_red_random_blue.yaml \
    --output-dir ./traces \
    --num-traces 1000 \
    --max-steps 30
```

### Train and Evaluate DFAs

```bash
python evaluation/incremental_learning.py \
    --training-dir ./traces/train \
    --eval-dir ./traces/test \
    --output-dir ./learned_dfas \
    --max-traces 500 \
    --step 50
```

## Project Structure

```
BabyCyborg/
├── cage0/                          # Core simulation framework
│   ├── simulator.py                # Main ModularCage0Sim class
│   ├── agents/                     # Agent definitions
│   │   ├── agent_generator.py      # YAML → Agent class generator
│   │   ├── base_agent.py           # Abstract agent interface
│   │   ├── red_agents/             # Red agent YAML + Python files
│   │   └── blue_agents/            # Blue agent YAML + Python files
│   ├── actions/                    # Action implementations
│   └── core/                       # Core components
│       ├── state_manager.py        # State tracking
│       ├── action_executor.py      # Action execution
│       ├── referee.py              # Monitor coordination
│       └── monitor.py              # Monitor base class
├── yaml_files/                     # YAML configurations
│   ├── config/                     # Scenario configs (5 configs)
│   ├── monitors/                   # Monitor definitions
│   └── network_config/             # Network topology
├── evaluation/                     # DFA learning and evaluation
│   ├── evaluator.py                # DFA evaluation
│   └── incremental_learning.py     # Incremental DFA training
├── scripts/                        # CLI tools
│   ├── eval_cage0.py               # Run simulations
│   ├── generate_traces.py          # Generate training traces
│   └── evaluate_dfas_on_traces.py  # Evaluate learned DFAs
├── sim_learn/                      # RPNI learning integration
├── tests/                          # Unit tests (96 tests)
└── data/                           # Datasets
```

## Available Configurations

| Config | Red Agent | Blue Agent |
|--------|-----------|------------|
| `one_host_random_red_random_blue.yaml` | Random on host 0 | Remove_0 or NoOp |
| `two_host_heuristic_red_random_blue.yaml` | Heuristic kill-chain on hosts 0-1 | Remove_0/1 or NoOp |
| `four_host_heuristic_red_random_blue.yaml` | Heuristic kill-chain on all hosts | Remove_0/1/2/3 or NoOp |
| `four_host_random_red_random_blue.yaml` | Random on all hosts | Remove_0/1/2/3 or NoOp |
| `test_minimal.yaml` | Random on host 0 | Remove_0 or NoOp (no monitors) |

## Red Agent Kill Chain

Red agents follow the attack sequence: **DRS → DNS → ERS → PE → Impact**

- **DRS** (DiscoverRemoteSystems) - Discover all hosts
- **DNS** (DiscoverNetworkServices) - q0 → q1
- **ERS** (ExploitRemoteService) - q1 → q2
- **PE** (PrivilegeEscalate) - q2 → q3
- **Impact** - Execute from q3

## Python API

```python
from cage0.simulator import ModularCage0Sim

# Initialize and run
sim = ModularCage0Sim('yaml_files/config/four_host_heuristic_red_random_blue.yaml', max_steps=30)
sim.reset()
sim.create_yaml_agents()

for _ in range(30):
    result = sim.auto_step()
    if result['done']:
        break

# Get trace for RPNI learning
trace = sim.get_trace()
```

## Running Tests

```bash
python -m pytest tests/ -v
```

## Requirements

- Python 3.8+
- aalpy
- graphviz
- pytest

## License

MIT License
