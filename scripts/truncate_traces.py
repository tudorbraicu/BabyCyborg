#!/usr/bin/env python3
"""Truncate traces to N steps and copy to destination."""
import ast
import os
import sys

src_dir = sys.argv[1]
dst_dir = sys.argv[2]
max_steps = int(sys.argv[3])
num_files = int(sys.argv[4])

os.makedirs(dst_dir, exist_ok=True)

for i in range(1, num_files + 1):
    src = os.path.join(src_dir, f'output_{i}.txt')
    dst = os.path.join(dst_dir, f'output_{i}.txt')
    with open(src, 'r') as f:
        trace = ast.literal_eval(f.read())
    trace[0] = trace[0][:max_steps]
    with open(dst, 'w') as f:
        f.write(str(trace))
    if i % 5000 == 0:
        print(f'Progress: {i}/{num_files}')

print(f'Done! Truncated {num_files} traces to {max_steps} steps')
