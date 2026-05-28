# BabyCyborg

A small, YAML-driven cybersecurity simulator for studying red/blue agent interactions and learning their behavior as finite-state automata.

## Structure

- `cage0/` — the simulator.
- `yaml_files/` — scenario configs, monitor rules, and network topology.
- `sim_learn/` — RPNI-based automata learner (`learn_automata.py`) and DFA visualizer (`visualize_dfa.py`).
- `evaluation/` — `evaluator.py` (replay-based scoring of a learned DFA) and `incremental_learning.py` (training on growing batches).
- `scripts/` — CLI helpers: run an episode, generate or truncate traces, evaluate DFAs.

## Quick start

Run a single episode:

```bash
python scripts/eval_cage0.py \
    --scenario yaml_files/config/one_host_random_red_random_blue.yaml \
    --max-steps 20
```

Available scenarios: `one_host_random_red_random_blue.yaml`, `one_host_heuristic_red_random_blue.yaml`, `two_host_heuristic_red_random_blue.yaml`. New scenarios, agents (YAML or Python), and monitors are drop-in.

## CAV 2026 artifact

The frozen reproducibility artifact for *"The Simulator's Blueprint: Automata Learning from System Event Logs"* (Docker image, raw CAGE2 traces, scripts to reproduce the paper's figures and tables) is on Zenodo: [10.5281/zenodo.19828945](https://doi.org/10.5281/zenodo.19828945).

## Requirements

Python 3.9+, `aalpy`, `graphviz`.

## License

MIT.
