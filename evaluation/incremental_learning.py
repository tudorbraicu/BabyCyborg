#!/usr/bin/env python3
"""
Incremental DFA Learning and Evaluation

Trains DFAs incrementally on 1 to 20 traces, evaluates each on test traces,
and records state counts and accuracies for visualization.

Supports parallel execution with --cpus flag to learn multiple checkpoints simultaneously.
"""

import sys
import os
import json
import threading
from multiprocessing import Pool, cpu_count, Manager

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'sim_learn'))
sys.path.insert(0, os.path.dirname(__file__))

from learn_automata import SimulatorLearner
from aalpy.utils import save_automaton_to_file
from evaluator import DFAEvaluator


def learn_single_checkpoint(args):
    """
    Learn and evaluate a single checkpoint (for parallel execution).

    Args:
        args: tuple of (num_traces, training_dir, eval_dir, output_dir)

    Returns:
        dict with results for this checkpoint
    """
    num_traces, training_dir, eval_dir, output_dir = args

    # Get file paths for traces 1 to num_traces
    training_files = [
        os.path.join(training_dir, f"output_{j}.txt")
        for j in range(1, num_traces + 1)
    ]

    # Check that all files exist
    missing_files = [f for f in training_files if not os.path.exists(f)]
    if missing_files:
        return {
            'num_traces': num_traces,
            'error': f"Missing files: {missing_files[:3]}..."
        }

    try:
        # Train DFA
        learner = SimulatorLearner()
        learner.learn_logs(training_files)
        dfa_sim = learner.get_dfa_sim()

        # Save to .dot file
        dot_filename = os.path.join(output_dir, f"learned_dfa_{num_traces}traces.dot")
        save_automaton_to_file(dfa_sim, path=dot_filename)

        # Record state count
        state_count = len(dfa_sim.states)

        # Evaluate on all test traces in eval_dir
        evaluator = DFAEvaluator(dot_filename)
        accuracies = []

        # Find all trace files in eval_dir
        test_num = 0
        while True:
            test_num += 1
            test_path = os.path.join(eval_dir, f"trace{test_num}.txt")

            if not os.path.exists(test_path):
                break

            try:
                result = evaluator.evaluate_trace(test_path, debug=False)
                accuracies.append(result['accuracy'])
            except Exception:
                continue

        # Calculate average accuracy
        avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0.0

        print(f"[{num_traces} traces] {state_count} states, {avg_accuracy:.2%} accuracy")

        return {
            'num_traces': num_traces,
            'state_count': state_count,
            'avg_accuracy': avg_accuracy
        }

    except Exception as e:
        return {
            'num_traces': num_traces,
            'error': str(e)
        }


def incremental_learning(max_traces=20, start_from=1, step=1, output_dir=None, training_dir=None, eval_dir=None, cpus=1):
    """
    Train DFAs incrementally and evaluate on test traces.

    Args:
        max_traces: Maximum number of traces to train on (default: 20)
        start_from: Start training from this many traces (default: 1)
        step: Evaluate every N traces (default: 1)
        output_dir: Directory to save .dot files and results (default: incremental_learning_data)
        training_dir: Directory containing training traces (default: sim-learn/logs/training_traces)
        eval_dir: Directory containing evaluation traces (default: evaluation/eval_traces)
        cpus: Number of CPUs for parallel execution (default: 1 = sequential)
    """
    # Set default directories (relative to one_host_setup)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    one_host_dir = os.path.join(script_dir, "one_host_setup")

    if output_dir is None:
        output_dir = os.path.join(one_host_dir, "learned_dfas")
    if training_dir is None:
        training_dir = os.path.join(one_host_dir, "training_traces")
    if eval_dir is None:
        eval_dir = os.path.join(one_host_dir, "eval_traces")

    # Create output directory if needed
    os.makedirs(output_dir, exist_ok=True)

    # Load existing results if file exists (for resume functionality)
    results_path = os.path.join(output_dir, 'incremental_results.json')
    existing_results = []
    existing_num_traces = set()
    if os.path.exists(results_path):
        try:
            with open(results_path, 'r') as f:
                existing_results = json.load(f)
                existing_num_traces = {r['num_traces'] for r in existing_results if 'num_traces' in r}
                print(f"Loaded {len(existing_results)} existing results from {results_path}")
        except Exception as e:
            print(f"Warning: Could not load existing results: {e}")
            existing_results = []

    # Generate list of checkpoints to evaluate
    checkpoints = list(range(start_from, max_traces + 1, step))
    print(f"Will evaluate {len(checkpoints)} checkpoints: {checkpoints[0]} to {checkpoints[-1]} (step={step})")
    print(f"Using {cpus} CPU(s)")

    if cpus > 1:
        # Parallel execution with incremental saving
        print(f"\n{'='*60}")
        print(f"Running {len(checkpoints)} checkpoints in parallel on {cpus} CPUs...")
        print(f"Results will be saved incrementally as workers complete.")
        print(f"{'='*60}\n")

        # Prepare arguments for each checkpoint
        args_list = [
            (num_traces, training_dir, eval_dir, output_dir)
            for num_traces in checkpoints
        ]

        # Use a lock for thread-safe file writing
        file_lock = threading.Lock()

        # Start with existing results
        all_results = {r['num_traces']: r for r in existing_results}
        completed_count = [0]  # Use list for mutable counter in closure

        def save_result(result):
            """Callback to save result as soon as worker completes."""
            with file_lock:
                if 'error' not in result:
                    all_results[result['num_traces']] = result
                    # Save incrementally
                    sorted_results = sorted(all_results.values(), key=lambda x: x['num_traces'])
                    with open(results_path, 'w') as f:
                        json.dump(sorted_results, f, indent=2)
                completed_count[0] += 1
                print(f"  Saved {completed_count[0]}/{len(checkpoints)} checkpoints to {results_path}")

        with Pool(cpus) as pool:
            # Use imap_unordered for results as they complete
            for result in pool.imap_unordered(learn_single_checkpoint, args_list):
                save_result(result)

        # Final results
        results = sorted(all_results.values(), key=lambda x: x['num_traces'])

        # Print error summary
        error_results = [r for r in pool.map(learn_single_checkpoint, args_list) if 'error' in r] if False else []
        # Check for errors in collected results
        error_count = len(checkpoints) - len([r for r in results if r['num_traces'] in checkpoints])
        if error_count > 0:
            print(f"\n{error_count} checkpoints had errors (not saved)")

    else:
        # Sequential execution (original behavior)
        # Start with existing results for merging
        results = list(existing_results)

        for i in checkpoints:
            print(f"\n{'='*60}")
            print(f"Training on {i} trace(s)")
            print(f"{'='*60}")

            # 1. Get file paths for traces 1 to i
            training_files = [
                os.path.join(training_dir, f"output_{j}.txt")
                for j in range(1, i + 1)
            ]

            # Check that all files exist
            missing_files = [f for f in training_files if not os.path.exists(f)]
            if missing_files:
                print(f"Warning: Missing training files: {missing_files}")
                print(f"Stopping at {i-step} traces")
                break

            # 2. Train DFA
            print(f"Loading {len(training_files)} trace file(s)...")
            learner = SimulatorLearner()

            try:
                learner.learn_logs(training_files)
                dfa_sim = learner.get_dfa_sim()
            except Exception as e:
                print(f"Error learning DFA: {e}")
                print(f"Stopping at {i-step} traces")
                break

            # 3. Save to .dot file
            dot_filename = os.path.join(output_dir, f"learned_dfa_{i}traces.dot")
            save_automaton_to_file(dfa_sim, path=dot_filename)
            print(f"Saved DFA to {dot_filename}")

            # 4. Record state count
            state_count = len(dfa_sim.states)
            print(f"DFA has {state_count} states")

            # 5. Evaluate on all test traces in eval_dir
            print(f"Evaluating on test traces...")
            evaluator = DFAEvaluator(dot_filename)
            accuracies = []

            # Find all trace files in eval_dir
            test_num = 0
            while True:
                test_num += 1
                test_path = os.path.join(eval_dir, f"trace{test_num}.txt")

                if not os.path.exists(test_path):
                    break  # No more traces

                try:
                    result = evaluator.evaluate_trace(test_path, debug=False)
                    accuracies.append(result['accuracy'])
                    print(f"  Trace {test_num}: {result['accuracy']:.2%} "
                          f"({result['correct']}/{result['total']} correct)")
                except Exception as e:
                    print(f"  Error evaluating trace {test_num}: {e}")
                    continue

            # Calculate average accuracy
            if accuracies:
                avg_accuracy = sum(accuracies) / len(accuracies)
                print(f"Average accuracy: {avg_accuracy:.2%}")
            else:
                avg_accuracy = 0.0
                print("No successful evaluations")

            # 6. Store results - use dict to handle duplicates, then convert back to sorted list
            new_result = {
                'num_traces': i,
                'state_count': state_count,
                'avg_accuracy': avg_accuracy
            }

            # Convert to dict for merging, add new result, convert back to sorted list
            results_dict = {r['num_traces']: r for r in results}
            results_dict[i] = new_result
            results = sorted(results_dict.values(), key=lambda x: x['num_traces'])

            # Save results incrementally after each evaluation
            with open(results_path, 'w') as f:
                json.dump(results, f, indent=2)

    # Save final results (already sorted from above)
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Complete! Results saved to {results_path}")
    print(f"{'='*60}")

    return results


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Incrementally train DFAs and evaluate performance"
    )
    parser.add_argument(
        "--max-traces",
        type=int,
        default=20,
        help="Maximum number of traces to train on (default: 20)"
    )
    parser.add_argument(
        "--start-from",
        type=int,
        default=1,
        help="Start training from this many traces (default: 1)"
    )
    parser.add_argument(
        "--step",
        type=int,
        default=1,
        help="Evaluate every N traces (default: 1)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="incremental_learning_data",
        help="Directory to save .dot files and results (default: incremental_learning_data)"
    )
    parser.add_argument(
        "--training-dir",
        type=str,
        default=None,
        help="Directory containing training traces"
    )
    parser.add_argument(
        "--eval-dir",
        type=str,
        default=None,
        help="Directory containing evaluation traces"
    )
    parser.add_argument(
        "--cpus",
        type=int,
        default=1,
        help="Number of CPUs for parallel execution (default: 1 = sequential)"
    )

    args = parser.parse_args()

    incremental_learning(
        max_traces=args.max_traces,
        start_from=args.start_from,
        step=args.step,
        output_dir=args.output_dir,
        training_dir=args.training_dir,
        eval_dir=args.eval_dir,
        cpus=args.cpus
    )


if __name__ == "__main__":
    main()
