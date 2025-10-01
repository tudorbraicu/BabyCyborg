# BabyCyborg YAML Schema Documentation

This document describes the complete YAML schema for defining agent and host DFAs in BabyCyborg.

## Overview

The YAML configuration defines:
- **Agent DFAs**: State machines controlling agent behavior
- **Host DFAs**: State machines representing host security states
- **Actions**: Operations that transition host states
- **Reactive Transitions**: Environment-triggered state changes

---

## Top-Level Structure

```yaml
Agents:
  Red: { ... }
  Blue: { ... }

States:
  - q0  # Host states
  - q1
  ...

Hosts:
  Host_0: { initial_state: q0 }
  ...

Topology:
  type: star
  num_hosts: 4
  hosts: [Host_0, Host_1, ...]
```

---

## Agent Configuration

### Required Fields

```yaml
Agents:
  AgentName:
    initial_state: s1      # Starting state for this agent
    states: [s1, s2, ...]  # List of all agent states
    transitions: { ... }   # Action-based DFA transitions
    actions: { ... }       # Host action definitions
```

### Optional Fields

```yaml
    reactive_transitions: { ... }  # Environment-triggered transitions
```

---

## Agent Transitions

Agent transitions are **action-driven**: the agent chooses an action, executes it, and the DFA advances based on success/failure.

### Basic Transition

```yaml
transitions:
  transition_name:
    action: "ActionName"       # Action to execute
    target_host: 0             # Host index (0-based)
    from_state: s1             # Current agent state
    on_success: s2             # Next state if action succeeds
    on_failure: s1             # Next state if action fails
```

### Hostless Actions

For actions that don't target a specific host (e.g., global monitoring):

```yaml
transitions:
  global_check:
    action: "NoOp"
    target_host: null          # Explicitly no target (action must be marked hostless)
    from_state: b1
    on_success: b2
    on_failure: b1
```

The action must be defined with `hostless: true` in the `actions` section.

---

## Reactive Transitions

Reactive transitions are **environment-triggered**: changes in host states automatically trigger agent state changes.

### Basic Reactive Transition

```yaml
reactive_transitions:
  detect_compromise:
    trigger: host_state_change     # Trigger type
    from_state: any                # Can trigger from any state (or specific state)
    condition:
      type: any_host_in_states     # Condition type
      states: [q2, q3]             # Host states to watch for
    to_state: b5                   # Target agent state
```

### Trigger Types

| Trigger | Description |
|---------|-------------|
| `host_state_change` | Triggered when any host changes state |
| *(extensible)* | Future: `action_result`, `time_threshold`, etc. |

### Condition Types

#### `any_host_in_states`

Triggers if **any** changed host is in one of the specified states.

```yaml
condition:
  type: any_host_in_states
  states: [q2, q3]  # Trigger if any host reaches q2 or q3
```

#### `all_hosts_in_states`

Triggers if **all** changed hosts are in one of the specified states.

```yaml
condition:
  type: all_hosts_in_states
  states: [q3]  # Trigger only if all changed hosts are fully compromised
```

#### `specific_host`

Triggers if a **specific host** reaches a specific state.

```yaml
condition:
  type: specific_host
  host_id: 0
  state: q3  # Trigger only if Host_0 reaches q3
```

---

## Host Actions

Host actions define how actions affect host state machines.

### Simple Transition

Fixed state transition:

```yaml
actions:
  ExploitRemoteService:
    from_state: q1        # Required current state (or "any")
    to_state: q2          # Target state after action
    reward: 1             # Reward for successful execution
```

### Same-State Transition

Action that doesn't change state:

```yaml
actions:
  NoOp:
    from_state: any
    to_state: same        # Stay in current state
    reward: 0
```

### Conditional Transitions

State transition depends on current state:

```yaml
actions:
  Remove:
    from_state: any
    to_state:
      q0: q0              # If host is secure, stay secure
      q1: q1              # If discovered, stay discovered
      default: q1         # All other states reset to q1
    reward: -1
```

The `default` key specifies the fallback if current state isn't explicitly listed.

### Hostless Actions

Actions that don't target a specific host:

```yaml
actions:
  GlobalScan:
    from_state: any
    to_state: same
    reward: 0
    hostless: true        # Mark as hostless
```

When an action is marked `hostless: true`:
- Agent transitions can use `target_host: null`
- The action is still executed on host 0 (placeholder)
- Intended for actions with global effects

---

## Complete Example

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
      exploit:
        action: "ExploitRemoteService"
        target_host: 0
        from_state: s2
        on_success: s3
        on_failure: s2
    actions:
      DiscoverNetworkServices:
        from_state: q0
        to_state: q1
        reward: 0
      ExploitRemoteService:
        from_state: q1
        to_state: q2
        reward: 1

  Blue:
    initial_state: b1
    states: [b1, b2, b3]
    transitions:
      monitor:
        action: "NoOp"
        target_host: null  # Hostless
        from_state: b1
        on_success: b2
        on_failure: b1
      respond:
        action: "Remove"
        target_host: 0
        from_state: b3
        on_success: b1
        on_failure: b3
    reactive_transitions:
      detect_threat:
        trigger: host_state_change
        from_state: any
        condition:
          type: any_host_in_states
          states: [q2]
        to_state: b3  # Jump to response state
    actions:
      NoOp:
        from_state: any
        to_state: same
        reward: 0
        hostless: true
      Remove:
        from_state: any
        to_state:
          q0: q0
          default: q1
        reward: -1

States:
  - q0  # Secure
  - q1  # Discovered
  - q2  # Compromised

Hosts:
  Host_0:
    initial_state: q0

Topology:
  type: star
  num_hosts: 1
  hosts: [Host_0]
```

---

## Design Patterns

### Pattern 1: Linear Attack Chain

Red agent follows a strict sequence:

```yaml
Red:
  transitions:
    step1: { from_state: s1, on_success: s2, on_failure: s1, ... }
    step2: { from_state: s2, on_success: s3, on_failure: s2, ... }
    step3: { from_state: s3, on_success: s4, on_failure: s3, ... }
```

### Pattern 2: Monitoring Cycle

Blue agent cycles through states:

```yaml
Blue:
  transitions:
    monitor1: { from_state: b1, on_success: b2, ... }
    monitor2: { from_state: b2, on_success: b3, ... }
    monitor3: { from_state: b3, on_success: b1, ... }  # Back to start
```

### Pattern 3: Interrupt-Driven Response

Blue agent interrupts normal cycle on threat:

```yaml
Blue:
  transitions:
    # Normal cycle: b1 -> b2 -> b3 -> b1
  reactive_transitions:
    emergency:
      from_state: any  # Can interrupt any state
      condition: { type: any_host_in_states, states: [q2, q3] }
      to_state: b_emergency
```

---

## Validation Rules

1. **Agent States**:
   - All states in `transitions` must be listed in `states`
   - `initial_state` must be in `states`

2. **Transitions**:
   - `from_state` must match current agent state
   - `on_success` and `on_failure` must be valid states
   - `target_host` must be valid index (0 to num_hosts-1) or `null` for hostless

3. **Actions**:
   - Action name in transition must be defined in `actions`
   - `from_state` must be valid host state or "any"
   - `to_state` must be valid host state, "same", or conditional dict

4. **Conditional Transitions**:
   - Must have `default` key if not all host states are covered
   - All state keys must be valid host states

---

## Architecture Notes

### State Ownership

- **StateManager** owns all state (agent DFAs + host DFAs)
- **GeneratedAgent** queries state and returns actions (stateless)
- **ActionExecutor** executes actions and triggers state updates

### Execution Flow

```
1. Agent.get_action() → queries StateManager → returns {action, host}
2. Simulator.step(action, host) → calls ActionExecutor
3. ActionExecutor.execute_action() → updates host state
4. ActionExecutor → calls StateManager.update_agent_state()
5. StateManager → applies on_success/on_failure or reactive transitions
```

### Why This Design?

- **Single source of truth**: StateManager eliminates state conflicts
- **YAML-driven**: Zero hardcoded agent logic
- **Extensible**: New condition types and trigger types easy to add
- **Testable**: Clear separation of concerns
