"""
Example: a fully scripted workflow (no interactive input needed).

Shows the agent chaining two tools on its own - fetching data from an API
and writing a derived file to the workspace - from a single natural-language
task description. Run with:

    python -m workflows.example_workflow
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import check_api_key
from agent import Agent

TASK = """\
Fetch https://api.github.com/repos/anthropics/anthropic-sdk-python via \
http_request, then write a file called repo_summary.md in the workspace \
containing the repo's name, description, and star count, formatted as a \
short markdown bullet list."""


def main():
    check_api_key()
    agent = Agent()
    result = agent.run(TASK)
    print("\n=== Final result ===")
    print(result)


if __name__ == "__main__":
    main()
