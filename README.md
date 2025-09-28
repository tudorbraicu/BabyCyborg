# cage0 – minimal MILI-friendly cyber game simulator

## Layout
```
cage0/
  cage0/
    __init__.py
    core/
      types.py        # enums & dataclasses (HostState, AgentID, Actions, StepResult)
      topology.py     # StarTopology placeholder (future cross-host effects)
      simulator.py    # Cage0Sim: fixed-horizon, MILI-style reset, invalid actions no-op
    agents/
      base.py         # BaseAgent interface (act(sim) -> (host_idx, action))
      fixed.py        # FixedRedAgent / FixedBlueAgent (always return one action)
    io/
      trace.py        # Trace/TraceEntry + JSON export
  scripts/
    run.py            # CLI: run one episode and optionally write a JSON trace
```

## Quickstart
```
python -m cage0.scripts.run --num-hosts 4 --max-steps 20 --trace-out /tmp/trace.json
```
