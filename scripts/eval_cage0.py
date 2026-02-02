"""Simple CLI for running BabyCyborg episodes with YAML-defined DFA agents."""
import argparse
import sys
import os

# Add parent directory to path so we can import cage0
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from cage0.simulator import ModularCage0Sim


def run_with_yaml_agents(scenario_path, max_steps, verbose, agent_overrides=None):
    """Run simulation using YAML-defined DFA agents."""

    # Initialize environment
    env = ModularCage0Sim(scenario_path, max_steps, agent_overrides)
    env.reset()

    # Create YAML agents
    env.create_yaml_agents()
    red_agent = env.get_yaml_agent("Red")
    blue_agent = env.get_yaml_agent("Blue")

    if red_agent is None or blue_agent is None:
        # print("Error: Scenario YAML must define both Red and Blue agents")
        return None

    # Get initial state vector: [host_states..., agent_states..., monitor_states...]
    initial_state_vector = env.get_full_state_vector()
    num_agents = len(env.engine.agent_names)
    monitor_states = env.get_monitor_states()
    num_monitors = len(monitor_states)

    host_states = initial_state_vector[:env.num_hosts]
    agent_states_in_vector = initial_state_vector[env.num_hosts:env.num_hosts + num_agents]
    monitor_states_in_vector = initial_state_vector[env.num_hosts + num_agents:] if num_monitors > 0 else []

    # print(f"Initial state vector: {initial_state_vector}")
    # print(f"  ├─ Hosts ({env.num_hosts}): {host_states}")
    # print(f"  ├─ Agents ({num_agents}): {agent_states_in_vector} (Red={env.get_agent_states()['Red']}, Blue={env.get_agent_states()['Blue']})")
    # if monitor_states:
    #     sorted_monitor_names = sorted(monitor_states.keys())
    #     monitor_str = ", ".join(f"{name}={monitor_states[name]}" for name in sorted_monitor_names)
    #     print(f"  └─ Monitors ({num_monitors}): {monitor_states_in_vector} ({monitor_str})")
    # print(f"\nRed agent: YAML DFA ({red_agent})")
    # print(f"Blue agent: YAML DFA ({blue_agent})")
    # print("=" * 70)

    # Main loop using auto_step
    step_count = 0
    while step_count < max_steps:
        step_count += 1

        # Get current states before step
        state_vector_before = env.get_full_state_vector()
        agent_states_before = env.get_agent_states()
        monitor_states_before = env.get_monitor_states()
        num_agents = len(env.engine.agent_names)
        num_monitors = len(monitor_states_before)
        host_states_before = state_vector_before[:env.num_hosts]

        # Execute both agents' actions
        res = env.auto_step()

        # Extract action information
        red_action_info = res['last_actions']['Red']
        blue_action_info = res['last_actions']['Blue']

        # Get states after step
        state_vector_after = env.get_full_state_vector()
        agent_states_after = env.get_agent_states()
        monitor_states_after = env.get_monitor_states()
        host_states_after = state_vector_after[:env.num_hosts]

        # Display results
        # if verbose:
        #     print(f"Step {step_count}:")
        #     print(f"  State Vector: {state_vector_before} → {state_vector_after}")
        #     print(f"  ├─ Host States: {host_states_before} → {host_states_after}")
        #     print(f"  ├─ Agent States: Red {agent_states_before['Red']}→{agent_states_after['Red']}, "
        #           f"Blue {agent_states_before['Blue']}→{agent_states_after['Blue']}")
        #     if monitor_states_after:
        #         # Format monitor states with vector indices
        #         sorted_monitor_names = sorted(monitor_states_after.keys())
        #         monitor_str = ", ".join(f"{name}={monitor_states_after[name]}" for name in sorted_monitor_names)
        #         monitor_vector_after = state_vector_after[env.num_hosts + num_agents:]
        #         monitor_vector_before = state_vector_before[env.num_hosts + num_agents:]
        #         print(f"  └─ Monitor States: {monitor_vector_before} → {monitor_vector_after} ({monitor_str})")
        #     print(f"  Actions:")
        #     print(f"    Red: {red_action_info['action']}(host {red_action_info['host']}) | Reward: {red_action_info['reward']}")
        #     print(f"    Blue: {blue_action_info['action']}(host {blue_action_info['host']}) | Reward: {blue_action_info['reward']}")
        #     print("-" * 70)
        # else:
        #     # Format monitor states compactly for non-verbose output
        #     monitor_str = ""
        #     if monitor_states_after:
        #         monitor_str = " | M:" + ",".join(f"{name.split('_')[0]}[{state}]" for name, state in monitor_states_after.items())
        #     print(f"Step {step_count}: "
        #           f"Red[{agent_states_after['Red']}]→{red_action_info['action']}(h{red_action_info['host']}) | "
        #           f"Blue[{agent_states_after['Blue']}]→{blue_action_info['action']}(h{blue_action_info['host']}) | "
        #           f"R:{red_action_info['reward']:.0f}/{blue_action_info['reward']:.0f} | "
        #           f"Hosts:{host_states_after}{monitor_str}")

        if res['done']:
            break

    # Show final results
    # print("=" * 70)
    # print(f"Simulation completed after {step_count} steps")
    # reward_summary = env.get_reward_summary()
    # print(f"Final rewards: {reward_summary['total_rewards']}")
    # print(f"Total reward: {env.get_total_reward():.1f}")

    # Show complete final state
    # final_state_vector = env.get_full_state_vector()
    # final_agent_states = env.get_agent_states()
    # final_monitor_states = env.get_monitor_states()
    # num_agents = len(env.engine.agent_names)
    # num_monitors = len(final_monitor_states)

    # final_host_states = final_state_vector[:env.num_hosts]
    # final_agent_states_vector = final_state_vector[env.num_hosts:env.num_hosts + num_agents]
    # final_monitor_states_vector = final_state_vector[env.num_hosts + num_agents:] if num_monitors > 0 else []

    # print(f"\nFinal state vector: {final_state_vector}")
    # print(f"  ├─ Hosts ({env.num_hosts}): {final_host_states}")
    # print(f"  ├─ Agents ({num_agents}): {final_agent_states_vector} (Red={final_agent_states['Red']}, Blue={final_agent_states['Blue']})")
    # if final_monitor_states:
    #     sorted_monitor_names = sorted(final_monitor_states.keys())
    #     monitor_str = ", ".join(f"{name}={final_monitor_states[name]}" for name in sorted_monitor_names)
    #     print(f"  └─ Monitors ({num_monitors}): {final_monitor_states_vector} ({monitor_str})")

    # Get the detailed trace from the simulator
    trace = env.get_trace()

    # Group trace by steps for the nested list format
    episode_trace = []
    steps = {}
    for entry in trace:
        step = entry['step']
        if step not in steps:
            steps[step] = []
        steps[step].append(entry)

    # Create nested list: [step1_actions, step2_actions, ...]
    for step_num in sorted(steps.keys()):
        episode_trace.append(steps[step_num])

    return [episode_trace]




def main():
    # Parse arguments
    ap = argparse.ArgumentParser(
        description="Run BabyCyborg episode with YAML-defined DFA agents.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/eval_cage0.py --scenario yaml_files/config/cage0_scenario.yaml --max-steps 20
  python scripts/eval_cage0.py --scenario yaml_files/config/test_no_monitors.yaml --max-steps 15 --verbose
  python scripts/eval_cage0.py --scenario yaml_files/config/cage0_scenario.yaml --red-agent custom_red.yaml
        """
    )

    ap.add_argument("--scenario", type=str, required=True, help="Path to scenario YAML file")
    ap.add_argument("--max-steps", type=int, default=20, help="Maximum episode length")
    ap.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    ap.add_argument("--red-agent", type=str, default=None, help="Override Red agent with custom agent file (relative to scenario dir)")
    ap.add_argument("--blue-agent", type=str, default=None, help="Override Blue agent with custom agent file (relative to scenario dir)")
    args = ap.parse_args()

    # Build agent overrides dictionary
    agent_overrides = {}
    if args.red_agent:
        agent_overrides['Red'] = args.red_agent
    if args.blue_agent:
        agent_overrides['Blue'] = args.blue_agent

    # Run simulation
    # print("Running BabyCyborg simulation with YAML-defined DFA agents...\n")
    # if agent_overrides:
    #     print(f"Agent overrides: {agent_overrides}\n")
    acts = run_with_yaml_agents(args.scenario, args.max_steps, args.verbose, agent_overrides if agent_overrides else None)

    # Print traces in list format
    if acts:
        # print("\nTraces:")
        print(acts)


if __name__ == "__main__":
    main()
