"""
Shell command tool - the most powerful (and dangerous) tool available.

This is OFF by default. It only registers itself if you explicitly set
AGENT_ALLOW_SHELL=1 in the environment, so an agent never gets shell access
by accident. Even when enabled, commands run with a timeout and only their
tail output is returned.
"""

import os
import subprocess

from tools.registry import tool

SHELL_ENABLED = os.environ.get("AGENT_ALLOW_SHELL", "0") == "1"
COMMAND_TIMEOUT_SECONDS = 20

if SHELL_ENABLED:

    @tool(
        name="run_shell_command",
        description=(
            "Run a shell command on the local machine and return its exit "
            "code, stdout, and stderr. Use for automation tasks such as "
            "running scripts, checking file/system state, or invoking CLI "
            "tools. Commands time out after 20 seconds."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute.",
                }
            },
            "required": ["command"],
        },
    )
    def run_shell_command(command: str) -> str:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=COMMAND_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return f"Error: command timed out after {COMMAND_TIMEOUT_SECONDS}s"

        stdout = result.stdout[-3000:]
        stderr = result.stderr[-1000:]
        return f"exit_code: {result.returncode}\nstdout:\n{stdout}\nstderr:\n{stderr}"
