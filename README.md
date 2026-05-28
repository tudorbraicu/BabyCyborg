# BabyCyborg

A small, YAML-driven cybersecurity simulator for studying red/blue agent interactions.

## Concepts

BabyCyborg models a small cybersecurity scenario with two adversaries on a network of hosts:

- **Agents.** A *Red* agent attacks (e.g. discover → exploit → privilege-escalate → impact); a *Blue* agent defends (e.g. remove the attacker, no-op). Each is a finite-state automaton, written in YAML by default and dropping into Python only for more complex behavior. They live in `cage0/agents/red_agents/` and `cage0/agents/blue_agents/`.
- **Hosts and host states.** Every host moves through security states `q0` (clean) → `q1` (discovered) → `q2` (exploited) → `q3` (privilege-escalated). Red advances them; Blue resets them.
- **Monitors.** Rules that decide whether an action succeeds and whether host transitions are valid. Each scenario picks a monitor set: `yaml_files/monitors/active/` (the default per-host network-validity monitors) or `yaml_files/monitors/all_monitors/` (adds further blue-side restrictions).
- **Scenarios.** A YAML file in `yaml_files/config/` that wires a network topology to one Red agent, one Blue agent, and a monitor set. Pick a scenario and the simulator does the rest.

## Structure

- `cage0/` — the simulator.
- `yaml_files/` — scenario configs, monitor rules, and network topology.
- `scripts/` — CLI helpers: run an episode (`eval_cage0.py`), generate or truncate traces (`generate_traces.py`, `truncate_traces.py`).

## Install

```bash
pip install -r requirements.txt
```

Python 3.9+.

## Quick start

Run a single episode (prints a trace to stdout):

```bash
python scripts/eval_cage0.py \
    --scenario yaml_files/config/one_host_random_red_random_blue.yaml \
    --max-steps 20
```

Available scenarios: `one_host_random_red_random_blue.yaml`, `one_host_heuristic_red_random_blue.yaml`, `two_host_heuristic_red_random_blue.yaml`. New scenarios, agents (YAML or Python), and monitors are drop-in.

### Generate traces

```bash
python scripts/generate_traces.py \
    --scenario yaml_files/config/one_host_heuristic_red_random_blue.yaml \
    --output-dir tmp_traces/ \
    --num-traces 1000 \
    --max-steps 30
```

This writes one `output_<i>.txt` per episode into `tmp_traces/`. Each file is a single-line Python literal of the shape `[[[blue, red], [blue, red], ...]]` — an outer list (always one episode), a middle list of step pairs, and inside each pair two dicts describing the blue and red actions. The first two steps of a one-episode trace look like:

```python
[[[{'episode': 1, 'step': 1, 'action': 'Remove', 'agent': 'Blue',
    'hostname': 'Host_2', 'ip_address': '10.0.100.12', 'success': 'TRUE'},
   {'episode': 1, 'step': 1, 'action': 'Impact', 'agent': 'Red',
    'hostname': 'Host_1', 'ip_address': '10.0.100.11', 'success': 'FALSE'}],
  [{'episode': 1, 'step': 2, 'action': 'Remove', 'agent': 'Blue',
    'hostname': 'Host_0', 'ip_address': '10.0.100.10', 'success': 'TRUE'},
   {'episode': 1, 'step': 2, 'action': 'DiscoverNetworkServices', 'agent': 'Red',
    'hostname': 'Host_1', 'ip_address': '10.0.100.11', 'success': 'FALSE'}],
  ...]]
```

## CAV 2026: automata-learning case study

The paper *"The Simulator's Blueprint: Automata Learning from System Event Logs"* uses BabyCyborg traces to learn deterministic finite automata via RPNI. The RPNI learner, the DFA evaluator, the raw CAGE2 traces, and the scripts that reproduce the paper's figures and tables are all packaged in the frozen reproducibility artifact on Zenodo: [10.5281/zenodo.19828945](https://doi.org/10.5281/zenodo.19828945).

## License

MIT, see `LICENSE`.
