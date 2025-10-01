"""Simple CLI for running baby CybORG episodes with agents.

Supports both:
- Hand-coded agents (legacy): killchain_red, random_red, etc.
- YAML DFA agents (new): Agents defined in scenario YAML file
"""
import argparse
import sys
import os

# Add parent directory to path so we can import cage0
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from cage0.modular_simulator import ModularCage0Sim


def run_with_yaml_agents(scenario_path, max_steps, verbose):
    """Run simulation using YAML-defined DFA agents."""

    # Initialize environment
    env = ModularCage0Sim(scenario_path, max_steps)
    env.reset()

    # Create YAML agents
    env.create_yaml_agents()
    red_agent = env.get_yaml_agent("Red")
    blue_agent = env.get_yaml_agent("Blue")

    if red_agent is None or blue_agent is None:
        print("Error: Scenario YAML must define both Red and Blue agents")
        return None

    print(f"Initial state: {env.state_manager.get_state_vector()}")
    print(f"Red agent: YAML DFA ({red_agent})")
    print(f"Blue agent: YAML DFA ({blue_agent})")
    print(f"Agent states: {env.get_agent_states()}")
    print("=" * 70)

    # Initialize trace collection
    episode_trace = []

    # Main loop using auto_step
    step_count = 0
    while step_count < max_steps:
        step_count += 1

        # Get current agent states before step
        agent_states_before = env.get_agent_states()
        host_states_before = env.state_manager.get_state_vector()[:env.num_hosts]

        # Execute both agents' actions
        res = env.auto_step()

        # Extract action information
        red_action_info = res['last_actions']['Red']
        blue_action_info = res['last_actions']['Blue']

        # Get states after step
        agent_states_after = env.get_agent_states()
        host_states_after = env.state_manager.get_state_vector()[:env.num_hosts]

        # Store actions in trace
        step_data = [
            {
                "episode": 1,
                "step": step_count,
                "action": red_action_info['action'],
                "agent": "Red",
                "host": red_action_info['host'],
                "reward": red_action_info['reward'],
                "agent_state_before": agent_states_before['Red'],
                "agent_state_after": agent_states_after['Red']
            },
            {
                "episode": 1,
                "step": step_count,
                "action": blue_action_info['action'],
                "agent": "Blue",
                "host": blue_action_info['host'],
                "reward": blue_action_info['reward'],
                "agent_state_before": agent_states_before['Blue'],
                "agent_state_after": agent_states_after['Blue']
            }
        ]
        episode_trace.append(step_data)

        # Display results
        if verbose:
            print(f"Step {step_count}:")
            print(f"  Agent States: Red {agent_states_before['Red']}→{agent_states_after['Red']}, "
                  f"Blue {agent_states_before['Blue']}→{agent_states_after['Blue']}")
            print(f"  Red: {red_action_info['action']}(host {red_action_info['host']}) | Reward: {red_action_info['reward']}")
            print(f"  Blue: {blue_action_info['action']}(host {blue_action_info['host']}) | Reward: {blue_action_info['reward']}")
            print(f"  Host States: {host_states_before} → {host_states_after}")
            print("-" * 70)
        else:
            print(f"Step {step_count}: "
                  f"Red[{agent_states_after['Red']}]→{red_action_info['action']}(h{red_action_info['host']}) | "
                  f"Blue[{agent_states_after['Blue']}]→{blue_action_info['action']}(h{blue_action_info['host']}) | "
                  f"R:{red_action_info['reward']:.0f}/{blue_action_info['reward']:.0f} | "
                  f"Hosts:{host_states_after}")

        if res['done']:
            break

    # Show final results
    print("=" * 70)
    print(f"Simulation completed after {step_count} steps")
    reward_summary = env.get_reward_summary()
    print(f"Final rewards: {reward_summary['total_rewards']}")
    print(f"Total reward: {env.get_total_reward():.1f}")
    print(f"Final agent states: {env.get_agent_states()}")
    print(f"Final host states: {env.state_manager.get_state_vector()[:env.num_hosts]}")

    return [episode_trace]


def run_with_hand_coded_agents(scenario_path, max_steps, red_agent_type, blue_agent_type, verbose):
    """Run simulation using hand-coded agents (legacy mode)."""

    from cage0.agents import create_agent

    # Initialize environment
    # Since env counts each agent action separately, multiply by 2 to get the desired number of cycles
    env = ModularCage0Sim(scenario_path, max_steps * 2)

    # Create hand-coded agents
    red_agent = create_agent(red_agent_type, name="Red")
    blue_agent = create_agent(blue_agent_type, name="Blue")

    initial_state = env.reset()
    print(f"Initial state: {initial_state}")
    print(f"Red agent: {red_agent.name} ({red_agent.__class__.__name__})")
    print(f"Blue agent: {blue_agent.name} ({blue_agent.__class__.__name__})")
    print("=" * 70)

    # Initialize trace collection
    episode_trace = []

    # Main loop
    step_count = 0
    while True:
        step_count += 1
        step_actions = []

        # Execute Red action
        current_state = env._hosts.copy()
        host_states = {i: state for i, state in enumerate(current_state)}
        red_action_info = red_agent.get_action(current_state, host_states, step_count)
        red_action = red_action_info['action']
        red_host = red_action_info['host']

        res = env.step(red_action, red_host)
        red_reward = res['reward']

        # Store Red action
        red_data = {
            "episode": 1,
            "step": step_count,
            "action": red_action,
            "agent": "Red",
            "host": red_host,
            "reward": red_reward
        }
        step_actions.append(red_data)

        if res['done']:
            episode_trace.append(step_actions)
            break

        # Execute Blue action
        current_state = env._hosts.copy()
        host_states = {i: state for i, state in enumerate(current_state)}
        blue_action_info = blue_agent.get_action(current_state, host_states, step_count)
        blue_action = blue_action_info['action']
        blue_host = blue_action_info['host']

        res = env.step(blue_action, blue_host)
        blue_reward = res['reward']

        # Store Blue action
        blue_data = {
            "episode": 1,
            "step": step_count,
            "action": blue_action,
            "agent": "Blue",
            "host": blue_host,
            "reward": blue_reward
        }
        step_actions.append(blue_data)

        # Add both actions to episode trace
        episode_trace.append(step_actions)

        # Display results
        if verbose:
            print(f"Step {step_count}:")
            print(f"  Red: {red_action}(host {red_host}) | Reward: {red_reward}")
            print(f"  Blue: {blue_action}(host {blue_host}) | Reward: {blue_reward}")
            print(f"  State: {res['state_vector']}")
            print("-" * 70)
        else:
            print(f"Step {step_count}: Red → {red_action}(h{red_host}) | Blue → {blue_action}(h{blue_host}) | "
                  f"R:{red_reward:.0f}/{blue_reward:.0f} | State: {res['state_vector']}")

        if res['done']:
            break

    # Show final results
    print("=" * 70)
    print(f"Simulation completed after {step_count} steps")
    print(f"Final total reward: {env.get_total_reward():.1f}")
    print(f"Final state: {res['state_vector']}")

    return [episode_trace]


def main():
    # Parse arguments
    ap = argparse.ArgumentParser(
        description="Run baby CybORG episode with agents.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use YAML-defined DFA agents (new):
  python scripts/eval_cage0.py --scenario scenarios/explicit_dfa.yaml --yaml-agents --max-steps 20

  # Use hand-coded agents (legacy):
  python scripts/eval_cage0.py --scenario scenarios/simple_star.yaml --red-agent killchain_red --blue-agent reactive_blue
        """
    )

    ap.add_argument("--scenario", type=str, help="Path to scenario YAML file")
    ap.add_argument("--max-steps", type=int, default=20, help="Maximum episode length")
    ap.add_argument("--yaml-agents", action="store_true",
                    help="Use YAML-defined DFA agents from scenario file (new mode)")
    ap.add_argument("--red-agent", type=str, default="killchain_red",
                    help="Red agent type for hand-coded mode: killchain_red, random_red, sleep")
    ap.add_argument("--blue-agent", type=str, default="reactive_blue",
                    help="Blue agent type for hand-coded mode: reactive_blue, proactive_blue, sleep")
    ap.add_argument("--list-agents", action="store_true",
                    help="List all available hand-coded agents and exit")
    ap.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = ap.parse_args()

    # List agents if requested
    if args.list_agents:
        try:
            from cage0.agents import AGENTS
            print("Hand-Coded Agents (Legacy Mode):")
            print("=" * 70)
            for agent_type, agent_class in AGENTS.items():
                print(f"  {agent_type:20} - {agent_class.__name__}")
                if hasattr(agent_class, '__doc__') and agent_class.__doc__:
                    doc_line = agent_class.__doc__.strip().split('\n')[0]
                    print(f"                         {doc_line}")
            print("\nYAML DFA Agents (New Mode):")
            print("=" * 70)
            print("  Agents are defined in the scenario YAML file under 'Agents' section")
            print("  Use --yaml-agents flag to enable this mode")
            print("\nExamples:")
            print("  python scripts/eval_cage0.py --scenario scenarios/explicit_dfa.yaml --yaml-agents")
            print("  python scripts/eval_cage0.py --scenario scenarios/simple_star.yaml --red-agent killchain_red")
        except ImportError:
            print("Note: Hand-coded agents (AGENTS dict) not available in new architecture")
            print("Use --yaml-agents mode with scenarios that define agents in YAML")
        return

    # Check that scenario is provided
    if not args.scenario:
        ap.error("--scenario is required unless using --list-agents")

    # Run simulation
    if args.yaml_agents:
        print("Running with YAML-defined DFA agents...\n")
        acts = run_with_yaml_agents(args.scenario, args.max_steps, args.verbose)
    else:
        print("Running with hand-coded agents (legacy mode)...\n")
        acts = run_with_hand_coded_agents(
            args.scenario, args.max_steps,
            args.red_agent, args.blue_agent, args.verbose
        )

    # Print traces in list format
    if acts:
        print("\nTraces:")
        print(acts)


if __name__ == "__main__":
    main()
