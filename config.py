"""
Loads environment variables from a .env file (if present) and does a quick
sanity check that an API key is set before the agent tries to make a call.
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()


def check_api_key() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit(
            "ANTHROPIC_API_KEY is not set.\n"
            "Copy .env.example to .env and add your key, or export it:\n"
            "  export ANTHROPIC_API_KEY=sk-ant-...\n"
            "Get a key at https://console.anthropic.com/"
        )
