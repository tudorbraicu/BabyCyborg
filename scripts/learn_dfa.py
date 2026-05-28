#!/usr/bin/env python3
"""Learn a DFA from a directory of trace files via RPNI."""
import sys
import os
import glob
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'sim_learn'))
from sim_learn.learn_automata import SimulatorLearner
from aalpy.utils import save_automaton_to_file


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--traces-dir', required=True,
                        help='Directory containing output_*.txt trace files')
    parser.add_argument('--output', default='learned_dfa.dot',
                        help='Output .dot path (default: learned_dfa.dot)')
    args = parser.parse_args()

    paths = sorted(glob.glob(os.path.join(args.traces_dir, 'output_*.txt')))
    if not paths:
        sys.exit(f'no output_*.txt files found in {args.traces_dir}')

    learner = SimulatorLearner()
    learner.learn_logs(paths)
    dfa = learner.get_dfa_sim()
    save_automaton_to_file(dfa, path=args.output)
    print(f'learned DFA with {len(dfa.states)} states from {len(paths)} traces; saved to {args.output}')


if __name__ == '__main__':
    main()
