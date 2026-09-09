"""
CLI entry point.

Usage:
    python main.py "Fetch https://api.github.com/repos/anthropics/anthropic-sdk-python and save the description field to repo_info.txt"
    python main.py                # interactive mode, one task per line
"""

import argparse

from config import check_api_key
from agent import Agent, DEFAULT_MODEL


def main():
    parser = argparse.ArgumentParser(description="Task-automation agent powered by the Claude API")
    parser.add_argument("task", nargs="*", help="Task to run. Omit for interactive mode.")
    parser.add_argument("--model", default=None, help=f"Model to use (default: {DEFAULT_MODEL})")
    parser.add_argument("--quiet", action="store_true", help="Suppress tool-call logging")
    args = parser.parse_args()

    check_api_key()
    agent = Agent(model=args.model, verbose=not args.quiet)

    if args.task:
        result = agent.run(" ".join(args.task))
        print("\n" + result)
        return

    print("Task-automation agent. Type a task and press enter, or 'exit' to quit.\n")
    while True:
        try:
            task = input("task> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if task.lower() in {"exit", "quit"}:
            break
        if not task:
            continue
        print(agent.run(task) + "\n")


if __name__ == "__main__":
    main()
