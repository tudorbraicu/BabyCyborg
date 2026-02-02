#!/usr/bin/env python3
"""Continue generating traces from a starting point."""
import sys
import os
from multiprocessing import Pool, cpu_count

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from scripts.eval_cage0 import run_with_yaml_agents

def generate_trace(args):
    i, scenario, max_steps, output_dir = args
    try:
        trace = run_with_yaml_agents(scenario, max_steps, False)
        if trace:
            with open(os.path.join(output_dir, f'output_{i}.txt'), 'w') as f:
                f.write(str(trace))
            return i, True
        return i, False
    except Exception as e:
        return i, str(e)

if __name__ == '__main__':
    scenario = sys.argv[1]
    output_dir = sys.argv[2]
    start = int(sys.argv[3])
    end = int(sys.argv[4])
    max_steps = int(sys.argv[5])
    cpus = int(sys.argv[6]) if len(sys.argv) > 6 else cpu_count()

    print(f"Generating traces {start} to {end} using {cpus} CPUs...")

    args_list = [(i, scenario, max_steps, output_dir) for i in range(start, end + 1)]

    with Pool(cpus) as pool:
        results = []
        for result in pool.imap_unordered(generate_trace, args_list):
            results.append(result)
            if len(results) % 1000 == 0:
                print(f"  Progress: {len(results)}/{end - start + 1}")

    success = sum(1 for _, r in results if r is True)
    print(f"Done! Generated {success}/{end - start + 1} traces")
