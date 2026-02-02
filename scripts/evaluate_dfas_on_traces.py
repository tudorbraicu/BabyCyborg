#!/usr/bin/env python3
"""Evaluate existing learned DFAs on a different eval set."""
import os
import sys
import json
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'evaluation'))
from evaluator import DFAEvaluator

def main():
    parser = argparse.ArgumentParser(description='Evaluate learned DFAs on traces')
    parser.add_argument('--dfa-dir', required=True, help='Directory with learned DFA .dot files')
    parser.add_argument('--eval-dir', required=True, help='Directory with eval traces')
    parser.add_argument('--output', required=True, help='Output JSON file')
    parser.add_argument('--start', type=int, default=1000, help='Start from this many traces')
    parser.add_argument('--step', type=int, default=1000, help='Step size')
    parser.add_argument('--max-traces', type=int, default=50000, help='Max traces')
    args = parser.parse_args()

    # Count eval traces
    num_eval = 0
    while os.path.exists(os.path.join(args.eval_dir, f'trace{num_eval + 1}.txt')):
        num_eval += 1
    print(f'Found {num_eval} eval traces in {args.eval_dir}')

    results = []
    for num_traces in range(args.start, args.max_traces + 1, args.step):
        dot_file = os.path.join(args.dfa_dir, f'learned_dfa_{num_traces}traces.dot')
        if not os.path.exists(dot_file):
            print(f'Skipping {num_traces} - no .dot file')
            continue

        evaluator = DFAEvaluator(dot_file)
        states = len(evaluator.dfa.states)
        accuracies = []

        for i in range(1, num_eval + 1):
            trace_path = os.path.join(args.eval_dir, f'trace{i}.txt')
            try:
                result = evaluator.evaluate_trace(trace_path, debug=False)
                accuracies.append(result['accuracy'])
            except Exception as e:
                pass

        avg_acc = sum(accuracies) / len(accuracies) if accuracies else 0
        print(f'{num_traces} traces: {avg_acc*100:.2f}% ({states} states)')
        results.append({
            'num_traces': num_traces,
            'avg_accuracy': avg_acc,
            'states': states
        })

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    print(f'\nSaved to {args.output}')

if __name__ == '__main__':
    main()
