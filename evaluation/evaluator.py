"""
DFA Evaluator for BabyCyborg

This module provides a blackbox interface to evaluate learned DFA simulators.
The DFA is loaded from a .dot file and evaluated against BabyCyborg traces.
"""

import ast
import json
from collections import defaultdict
from typing import Dict, List, Tuple, Any
from aalpy.utils import load_automaton_from_file
from aalpy.automata import Dfa


class DFAEvaluator:
    """
    Evaluator for learned DFA simulators.

    Takes a learned DFA (.dot file) and evaluates it against new BabyCyborg traces.
    """

    def __init__(self, dot_path: str):
        """
        Initialize the evaluator.

        Args:
            dot_path: Path to learned DFA .dot file
        """
        # Load the DFA
        self.dfa = load_automaton_from_file(dot_path, automaton_type='dfa')
        if self.dfa is None:
            raise ValueError(f"Failed to load DFA from {dot_path}")

        print(f"Loaded DFA with {len(self.dfa.states)} states")


    def parse_trace(self, trace_path: str) -> Tuple[List[Dict], List[bool]]:
        """
        Parse a BabyCyborg trace file.

        Returns:
            Tuple of (actions, actual_success_values)
            - actions: List of action dicts (episode/step/agent/success removed)
            - actual_success_values: List of boolean success values for comparison
        """
        actions = []
        actual_success = []

        with open(trace_path, 'r') as f:
            content = f.read().strip()

            if not (content.startswith('[') and content.endswith(']')):
                raise ValueError("Trace file not properly formatted")

            raw_data = ast.literal_eval(content)

        # Process in chronological step order: Blue then Red per step
        for step_actions in raw_data:
            if not isinstance(step_actions, list):
                continue

            for action_pair in step_actions:
                try:
                    blue_action = action_pair[0]  # Blue agent
                    red_action = action_pair[1]   # Red agent

                    # Process Blue action
                    blue_clean = {k: v for k, v in blue_action.items()
                                  if k not in ['episode', 'step', 'agent', 'success']}
                    actions.append(blue_clean)
                    actual_success.append(blue_action['success'] == 'TRUE')

                    # Process Red action
                    red_clean = {k: v for k, v in red_action.items()
                                 if k not in ['episode', 'step', 'agent', 'success']}
                    actions.append(red_clean)
                    actual_success.append(red_action['success'] == 'TRUE')

                except (KeyError, TypeError, IndexError) as e:
                    print(f"Warning: Skipping malformed action: {e}")
                    continue

        return actions, actual_success


    def apply_field_mapping(self, action: Dict) -> Tuple:
        """
        Extract fields in the correct order for DFA input.

        IMPORTANT: The saved .dot file contains the REMAPPED DFA from get_dfa_sim(),
        which expects ACTUAL VALUES (NoOp, Host_0) NOT simplified codes (a1, h1).
        So we just extract the raw values, no mapping needed!

        Args:
            action: Raw action dict (without episode/step/agent/success)

        Returns:
            Tuple representing the action in DFA input format
        """
        values = []

        # Action is always present
        if 'action' in action:
            values.append(action['action'])

        # Use hostname if present, otherwise use subnetname (for DiscoverRemoteSystems)
        if 'hostname' in action:
            values.append(action['hostname'])
        elif 'subnetname' in action:
            values.append(action['subnetname'])

        # Add exploit_class for ExploitRemoteService actions
        if 'exploit_class' in action:
            values.append(action['exploit_class'])

        return tuple(values)


    def evaluate_step_by_step(self, actions: List[Dict], debug=False) -> List[bool]:
        """
        Evaluate actions one-by-one through the DFA.

        Args:
            actions: List of parsed actions (without episode/step/agent/success)
            debug: If True, print debug information

        Returns:
            List of predicted success values (True/False) for each action
        """
        predictions = []
        cumulative_input = []

        for i, action in enumerate(actions):
            # Map action to DFA input format
            mapped_action = self.apply_field_mapping(action)

            # Build cumulative input (DFA was trained on cumulative traces)
            cumulative_input.extend(mapped_action)

            if debug and i < 3:
                print(f"\n--- Action {i} ---")
                print(f"Raw action: {action}")
                print(f"Mapped: {mapped_action}")
                print(f"Cumulative: {cumulative_input}")

            # Feed to DFA
            current_state = self.dfa.initial_state
            accepted = True

            for symbol in cumulative_input:
                if symbol in current_state.transitions:
                    current_state = current_state.transitions[symbol]
                else:
                    # Symbol not in DFA - reject
                    if debug and i < 3:
                        print(f"  REJECTED at symbol '{symbol}'")
                    accepted = False
                    break

            # Check if we're in accepting state
            if accepted and current_state.is_accepting:
                predictions.append(True)
                if debug and i < 3:
                    print(f"  ACCEPTED (state {current_state.state_id})")
            else:
                predictions.append(False)
                if debug and i < 3:
                    print(f"  REJECTED (accepted={accepted}, state={current_state.state_id if accepted else 'N/A'})")

        return predictions


    def evaluate_trace(self, trace_path: str, debug=False) -> Dict[str, Any]:
        """
        Complete evaluation of a trace file.

        Args:
            trace_path: Path to BabyCyborg trace file
            debug: If True, print debug information

        Returns:
            Dict containing:
                - predictions: List of predicted success values
                - actual: List of actual success values
                - accuracy: Overall accuracy
                - correct: Number of correct predictions
                - total: Total number of actions
                - details: List of per-action comparison
        """
        # Parse trace
        actions, actual_success = self.parse_trace(trace_path)

        # Get predictions
        predictions = self.evaluate_step_by_step(actions, debug=debug)

        # Compare predictions vs actual
        correct = sum(1 for pred, actual in zip(predictions, actual_success)
                     if pred == actual)
        total = len(predictions)
        accuracy = correct / total if total > 0 else 0.0

        # Per-action details
        details = []
        for i, (action, pred, actual) in enumerate(zip(actions, predictions, actual_success)):
            details.append({
                'action_index': i,
                'action': action,
                'predicted': pred,
                'actual': actual,
                'correct': pred == actual
            })

        return {
            'predictions': predictions,
            'actual': actual_success,
            'accuracy': accuracy,
            'correct': correct,
            'total': total,
            'details': details
        }


    def print_evaluation_summary(self, result: Dict[str, Any]):
        """
        Print a formatted evaluation summary.

        Args:
            result: Result dictionary from evaluate_trace()
        """
        print("\n" + "="*60)
        print("DFA EVALUATION SUMMARY")
        print("="*60)
        print(f"Total Actions: {result['total']}")
        print(f"Correct Predictions: {result['correct']}")
        print(f"Accuracy: {result['accuracy']:.2%}")
        print("="*60)

        # Show first few mismatches
        mismatches = [d for d in result['details'] if not d['correct']]
        if mismatches:
            print(f"\nFirst {min(5, len(mismatches))} mismatches:")
            for detail in mismatches[:5]:
                print(f"  Action {detail['action_index']}: "
                      f"Predicted={detail['predicted']}, "
                      f"Actual={detail['actual']}")
                print(f"    {detail['action']}")
        else:
            print("\nNo mismatches - perfect prediction!")
        print()


def main():
    """
    Example usage of DFAEvaluator.
    """
    import sys

    if len(sys.argv) < 3:
        print("Usage: python evaluator.py <dot_file> <trace_file>")
        sys.exit(1)

    dot_path = sys.argv[1]
    trace_path = sys.argv[2]

    # Create evaluator
    evaluator = DFAEvaluator(dot_path)

    # Evaluate trace
    result = evaluator.evaluate_trace(trace_path, debug=True)

    # Print summary
    evaluator.print_evaluation_summary(result)

    # Optionally save detailed results
    with open('evaluation_results.json', 'w') as f:
        # Convert to JSON-serializable format
        json_result = {k: v for k, v in result.items() if k != 'details'}
        json.dump(json_result, f, indent=2)
    print("Detailed results saved to evaluation_results.json")


if __name__ == '__main__':
    main()
