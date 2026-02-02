#!/usr/bin/env python
"""
Simple script to visualize a learned DFA from a .dot file.

Usage:
    python visualize_dfa.py <path_to_dot_file>

Example:
    python visualize_dfa.py ../evaluation/sophisticated_red_0_monitors/learned_dfas/learned_dfa_45traces.dot
"""

import sys
import os
from graphviz import Source

def visualize(dot_path):
    if not os.path.exists(dot_path):
        print(f"Error: File not found: {dot_path}")
        sys.exit(1)

    with open(dot_path) as f:
        src = Source(f.read())

    # Output path (same as input but without .dot extension)
    output_path = dot_path.replace('.dot', '')

    src.render(output_path, format='png', view=True)
    print(f"Saved to {output_path}.png")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Default to sophisticated_red_0_monitors 45 traces
        dot_path = "../evaluation/sophisticated_red_0_monitors/learned_dfas/learned_dfa_45traces.dot"
    else:
        dot_path = sys.argv[1]

    visualize(dot_path)
