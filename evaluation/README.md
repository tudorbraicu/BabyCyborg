# DFA Evaluation for BabyCyborg

Tools for training and evaluating learned DFA simulators on BabyCyborg traces.

## Files

- `evaluator.py` - Core DFAEvaluator class for evaluating a learned DFA against traces
- `incremental_learning.py` - Train DFAs incrementally and evaluate accuracy at each checkpoint
- `incremental_learning_true_false.py` - Same as above but with separate True/False prediction accuracy breakdown

## Usage

### Evaluator

```python
from evaluation import DFAEvaluator

evaluator = DFAEvaluator(dot_path="learned_dfa.dot")
result = evaluator.evaluate_trace("trace.txt")

print(f"Accuracy: {result['accuracy']:.2%}")
```

### Incremental Learning

```bash
python evaluation/incremental_learning.py \
    --training-dir ./data/train/ \
    --eval-dir ./data/test/ \
    --output-dir ./output/learned_dfas \
    --start-from 50 \
    --max-traces 1000 \
    --step 50
```

This trains DFAs at checkpoints (50, 100, 150, ... traces) and evaluates each on the test set, producing:
- `learned_dfa_Ntraces.dot` - DFA at each checkpoint
- `incremental_results.json` - State count and accuracy at each checkpoint

## Input Format

Trace files in BabyCyborg format:
```python
[[[{'action': 'NoOp', 'hostname': 'Host_0', 'success': 'TRUE', ...},
   {'action': 'DiscoverNetworkServices', 'hostname': 'Host_0', 'success': 'TRUE', ...}],
  ...]]
```

## Output

```python
{
    'predictions': [True, True, False, ...],
    'actual': [True, True, True, ...],
    'accuracy': 0.92,
    'correct': 55,
    'total': 60,
    'details': [...]
}
```

## Requirements

- aalpy
- graphviz
