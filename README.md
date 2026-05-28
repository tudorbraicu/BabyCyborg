# BabyCyborg

A small, YAML-driven cybersecurity simulator for studying red/blue agent interactions and learning their behavior as finite-state automata.

## Concepts

BabyCyborg models a small cybersecurity scenario with two adversaries on a network of hosts:

- **Agents.** A *Red* agent attacks (e.g. discover → exploit → privilege-escalate → impact); a *Blue* agent defends (e.g. remove the attacker, no-op). Each is a finite-state automaton, written in YAML by default and dropping into Python only for more complex behavior. They live in `cage0/agents/red_agents/` and `cage0/agents/blue_agents/`.
- **Hosts and host states.** Every host moves through security states `q0` (clean) → `q1` (discovered) → `q2` (exploited) → `q3` (privilege-escalated). Red advances them; Blue resets them.
- **Monitors.** Rules that decide whether an action succeeds and whether host transitions are valid. Each scenario picks a monitor set: `yaml_files/monitors/active/` (the default per-host network-validity monitors) or `yaml_files/monitors/all_monitors/` (adds further blue-side restrictions).
- **Scenarios.** A YAML file in `yaml_files/config/` that wires a network topology to one Red agent, one Blue agent, and a monitor set. Pick a scenario and the simulator does the rest.
- **The learned DFA.** From a batch of episode traces, the RPNI learner produces a single deterministic automaton that captures the joint Red+Blue interaction allowed under that scenario — essentially an inferred specification of how the system behaves.

## Structure

- `cage0/` — the simulator.
- `yaml_files/` — scenario configs, monitor rules, and network topology.
- `sim_learn/` — RPNI-based automata learner (`learn_automata.py`) and DFA visualizer (`visualize_dfa.py`).
- `evaluation/` — `evaluator.py` (replay-based scoring of a learned DFA) and `incremental_learning.py` (training on growing batches).
- `scripts/` — CLI helpers: run an episode (`eval_cage0.py`), generate or truncate traces (`generate_traces.py`, `truncate_traces.py`), learn a DFA (`learn_dfa.py`), evaluate DFAs (`evaluate_dfas_on_traces.py`).

## Install

```bash
pip install -r requirements.txt
```

Also install the `graphviz` system binary: `brew install graphviz` on macOS, `apt-get install graphviz` on Debian. Python 3.9+.

## Quick start

Run a single episode (prints a trace to stdout):

```bash
python scripts/eval_cage0.py \
    --scenario yaml_files/config/one_host_random_red_random_blue.yaml \
    --max-steps 20
```

Available scenarios: `one_host_random_red_random_blue.yaml`, `one_host_heuristic_red_random_blue.yaml`, `two_host_heuristic_red_random_blue.yaml`. New scenarios, agents (YAML or Python), and monitors are drop-in.

### Generate traces

No traces ship with this repo — you'll generate them yourself:

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

Alternatively, pull the 5000 pre-generated raw CAGE2 traces from the Zenodo artifact below.

### Learn a DFA from traces

```bash
python scripts/learn_dfa.py --traces-dir tmp_traces/ --output learned_dfa.dot
```

This runs RPNI on every `output_*.txt` in the directory and writes a Graphviz `.dot` automaton. Render to PNG with `python sim_learn/visualize_dfa.py learned_dfa.dot` (requires the Graphviz system binary).

Or programmatically:

```python
from sim_learn.learn_automata import SimulatorLearner
import glob

learner = SimulatorLearner()
learner.learn_logs(sorted(glob.glob('tmp_traces/output_*.txt')))
print('states:', len(learner.get_dfa_sim().states))
```

### Evaluate a learned DFA

Score a learned `.dot` automaton by replaying held-out traces through it and measuring how often its predictions match reality:

```python
from evaluation.evaluator import DFAEvaluator

evaluator = DFAEvaluator('path/to/learned.dot')
result = evaluator.evaluate_trace('tmp_traces/output_42.txt')
print(result)  # per-step matches, accuracy, etc.
```

## CAV 2026 artifact

The frozen reproducibility artifact for *"The Simulator's Blueprint: Automata Learning from System Event Logs"* (Docker image, raw CAGE2 traces, scripts to reproduce the paper's figures and tables) is on Zenodo: [10.5281/zenodo.19828945](https://doi.org/10.5281/zenodo.19828945).

## License

MIT, see `LICENSE`.
