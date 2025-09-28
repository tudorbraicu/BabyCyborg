"""Simple CLI for running baby CybORG episodes with sophisticated agents."""
import argparse
import sys
import os

# Add parent directory to path so we can import cage0
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from cage0.simulator import Cage0Sim
from cage0.agents import create_agent


def main():
    # Parse arguments
    ap = argparse.ArgumentParser(description="Run baby CybORG episode with agents.")
    ap.add_argument("--scenario", type=str, help="Path to scenario YAML file")
    ap.add_argument("--max-steps", type=int, default=20, help="Maximum episode length")
    ap.add_argument("--red-agent", type=str, default="killchain_red",
                    help="Red agent type: killchain_red, random_red, sleep")
    ap.add_argument("--blue-agent", type=str, default="reactive_blue",
                    help="Blue agent type: reactive_blue, proactive_blue, sleep")
    ap.add_argument("--list-agents", action="store_true",
                    help="List all available agents and exit")
    ap.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = ap.parse_args()

    # List agents if requested
    if args.list_agents:
        from cage0.agents import AGENTS
        print("Available Agents:")
        print("================")
        for agent_type, agent_class in AGENTS.items():
            print(f"  {agent_type:15} - {agent_class.__name__}")
            if hasattr(agent_class, '__doc__') and agent_class.__doc__:
                doc_line = agent_class.__doc__.strip().split('\n')[0]
                print(f"                    {doc_line}")
        print("\nExample usage:")
        print("  python scripts/run.py --scenario scenarios/simple_star.yaml --red-agent killchain_red --blue-agent reactive_blue")
        return

    # Check that scenario is provided if not just listing agents
    if not args.scenario:
        ap.error("--scenario is required unless using --list-agents")

    # Initialize environment and agents
    # Since env counts each agent action separately, multiply by 2 to get the desired number of cycles
    env = Cage0Sim(args.scenario, args.max_steps * 2)
    red_agent = create_agent(args.red_agent, name="Red")
    blue_agent = create_agent(args.blue_agent, name="Blue")

    initial_state = env.reset()
    print(f"Initial state: {initial_state}")
    print(f"Red agent: {red_agent.name} ({red_agent.__class__.__name__})")
    print(f"Blue agent: {blue_agent.name} ({blue_agent.__class__.__name__})")
    print("=" * 50)

    # Initialize trace collection
    acts = []
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
        if args.verbose:
            print(f"Step {step_count}:")
            print(f"  Red: {red_action}(host {red_host}) | Reward: {red_reward}")
            print(f"  Blue: {blue_action}(host {blue_host}) | Reward: {blue_reward}")
            print(f"  State: {res['state_vector']}")
            print("-" * 40)
        else:
            print(f"Step {step_count}: Red -> {red_action}(host {red_host}) | Blue -> {blue_action}(host {blue_host}) | "
                  f"Rewards: {red_reward}/{blue_reward} | State: {res['state_vector']}")

        if res['done']:
            break

    # Add episode trace to acts
    acts.append(episode_trace)

    # Show final results
    print("=" * 50)
    print(f"Simulation completed after {step_count} steps")
    print(f"Final total reward: {env.get_total_reward()}")
    print(f"Final state: {res['state_vector']}")

    # Print traces in list format like eval_lancer.py
    print("\nTraces:")
    print(acts)


if __name__ == "__main__":
    main()