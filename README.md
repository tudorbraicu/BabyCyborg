# BabyCyborg

A small, YAML-driven cybersecurity simulator for studying red/blue agent interactions and learning their behavior as finite-state automata.

## Structure

- `cage0/` — the simulator.
- `yaml_files/` — scenario configs, monitor rules, and network topology.
- `sim_learn/` — RPNI-based automata learner (`learn_automata.py`) and DFA visualizer (`visualize_dfa.py`).
- `evaluation/` — `evaluator.py` (replay-based scoring of a learned DFA) and `incremental_learning.py` (training on growing batches).
- `scripts/` — CLI helpers: run an episode, generate or truncate traces, evaluate DFAs.

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

This writes one `output_<i>.txt` per episode into `tmp_traces/` — each file is a single-line Python literal of `[blue, red]` step pairs. Alternatively, pull the 5000 pre-generated raw CAGE2 traces from the Zenodo artifact below.

### Learn a DFA from traces

```python
from sim_learn.learn_automata import SimulatorLearner
import glob

learner = SimulatorLearner()
learner.learn_logs(sorted(glob.glob('tmp_traces/output_*.txt')))
print('states:', len(learner.get_dfa_sim().states))
```

This runs RPNI and produces a `.dot` automaton. Render it to PNG with `python sim_learn/visualize_dfa.py path/to/file.dot` (requires the Graphviz system binary).

## CAV 2026 artifact

The frozen reproducibility artifact for *"The Simulator's Blueprint: Automata Learning from System Event Logs"* (Docker image, raw CAGE2 traces, scripts to reproduce the paper's figures and tables) is on Zenodo: [10.5281/zenodo.19828945](https://doi.org/10.5281/zenodo.19828945).

## License

MIT, see `LICENSE`.
