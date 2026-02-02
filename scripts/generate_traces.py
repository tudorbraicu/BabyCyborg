#!/usr/bin/env python3
"""Generate training traces for a given scenario."""
import sys
import os
import argparse
from multiprocessing import Pool, cpu_count

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from scripts.eval_cage0 import run_with_yaml_agents


def generate_trace(args):
    """Generate a single trace and save it."""
    i, scenario, max_steps, output_dir = args
    try:
        trace = run_with_yaml_agents(scenario, max_steps, False)
        if trace:
            output_path = os.path.join(output_dir, f'output_{i}.txt')
            with open(output_path, 'w') as f:
                f.write(str(trace))
            return i, True
        return i, False
    except Exception as e:
        return i, str(e)


def main():
    parser = argparse.ArgumentParser(description='Generate training traces')
    parser.add_argument('--scenario', type=str, required=True, help='Path to scenario YAML')
    parser.add_argument('--output-dir', type=str, required=True, help='Output directory for traces')
    parser.add_argument('--num-traces', type=int, default=1000, help='Number of traces to generate')
    parser.add_argument('--max-steps', type=int, default=15, help='Max steps per episode')
    parser.add_argument('--cpus', type=int, default=None, help='Number of CPUs (default: all)')
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    num_cpus = args.cpus or cpu_count()
    print(f"Generating {args.num_traces} traces using {num_cpus} CPUs...")
    print(f"Scenario: {args.scenario}")
    print(f"Output: {args.output_dir}")

    # Prepare arguments for each trace
    trace_args = [(i, args.scenario, args.max_steps, args.output_dir)
                  for i in range(1, args.num_traces + 1)]

    with Pool(num_cpus) as pool:
        results = []
        for result in pool.imap_unordered(generate_trace, trace_args):
            results.append(result)
            if len(results) % 5000 == 0:
                print(f"  Progress: {len(results)}/{args.num_traces}")

    success = sum(1 for _, r in results if r is True)
    print(f"\nDone! Generated {success}/{args.num_traces} traces")


if __name__ == '__main__':
    main()
