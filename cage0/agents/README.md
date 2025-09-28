# Cage0 Agents

This directory contains all agent implementations for the Cage0 simulator.

## Agent Structure

Each agent is implemented in its own file for better organization and maintainability:

### Base Classes
- **`base_agent.py`** - Abstract base class that all agents inherit from

### Red Team Agents
- **`random_red_agent.py`** - Takes random red team actions
- **`killchain_red_agent.py`** - Follows systematic kill chain progression:
  1. Discover services (q0 → q1)
  2. Exploit services (q1 → q2)
  3. Privilege escalate (q2 → q3)
  4. Impact (q3 → q3)

### Blue Team Agents
- **`reactive_blue_agent.py`** - Removes threats when they reach q2+ (configurable threshold)
- **`proactive_blue_agent.py`** - Immediately removes any non-q0 hosts

### Utility Agents
- **`sleep_agent.py`** - Always performs NoOp action (baseline/testing)

## Usage

```python
from cage0.agents import create_agent

# Create agents
red_agent = create_agent('killchain_red', name='Red')
blue_agent = create_agent('reactive_blue', name='Blue')

# Get action from agent
action_info = red_agent.get_action(state_vector, host_states, current_step)
```

## Available Agent Types

| Agent Type | Class | Description |
|------------|-------|-------------|
| `killchain_red` | KillchainRedAgent | Systematic red team progression |
| `random_red` | RandomRedAgent | Random red team actions |
| `reactive_blue` | ReactiveBlueAgent | Removes threats at threshold |
| `proactive_blue` | ProactiveBlueAgent | Removes any compromise immediately |
| `sleep` | SleepAgent | Does nothing (NoOp) |

## Adding New Agents

1. Create a new file `your_agent.py` in this directory
2. Inherit from `BaseAgent` and implement `get_action()` method
3. Add import and registry entry to `__init__.py`
4. Document the agent behavior

Example:
```python
from .base_agent import BaseAgent

class YourAgent(BaseAgent):
    def get_action(self, state_vector, host_states, current_step):
        # Your logic here
        return {'action': 'SomeAction', 'host': target_host}
```