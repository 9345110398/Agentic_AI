"""
Core agent loop.

The pattern here is the standard "agentic loop":
1. Send the conversation + available tools to Claude.
2. If Claude's response is plain text, we're done - return it.
3. If Claude's response asks to use one or more tools, run them locally,
   append the results to the conversation, and go back to step 1.
4. Stop after max_turns so a confused agent can't loop forever.

Everything the model can *do* lives in tools/ - this file only knows how
to run the loop, not what any individual tool does.
"""

import json
import os

from anthropic import Anthropic

from tools.registry import get_tool_schemas, execute_tool

# Import tool modules so their @tool decorators register themselves.
# (shell_tools only registers if AGENT_ALLOW_SHELL=1 is set.)
import tools.file_tools  # noqa: F401
import tools.http_tools  # noqa: F401
import tools.shell_tools  # noqa: F401

DEFAULT_MODEL = os.environ.get("AGENT_MODEL", "claude-sonnet-5")
DEFAULT_MAX_TURNS = 15
DEFAULT_MAX_TOKENS = 4096

DEFAULT_SYSTEM_PROMPT = """You are a task-automation agent. You have tools for \
reading/writing files in a sandboxed workspace, making HTTP requests to APIs, \
and (if enabled) running shell commands.

Guidelines:
- Break the task into concrete steps and use tools to make progress, rather \
than describing what you would do.
- Prefer the smallest number of tool calls that reliably completes the task.
- If a tool call fails, read the error and try a different approach instead \
of repeating the same call.
- When the task is complete, reply with plain text summarizing what you did \
and any relevant output - do not call a tool on the final turn.
- If the task is ambiguous or you're missing information you have no tool \
to obtain, say so and ask, rather than guessing at something consequential."""


class Agent:
    def __init__(
        self,
        system_prompt: str = None,
        model: str = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        verbose: bool = True,
    ):
        self.client = Anthropic()
        self.model = model or DEFAULT_MODEL
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        self.max_tokens = max_tokens
        self.verbose = verbose
        self.messages = []

    def run(self, task: str, max_turns: int = DEFAULT_MAX_TURNS) -> str:
        """Run the agent on a task until it produces a final text answer."""
        self.messages = [{"role": "user", "content": task}]

        for _ in range(max_turns):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self.system_prompt,
                tools=get_tool_schemas(),
                messages=self.messages,
            )
            self.messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason != "tool_use":
                return self._extract_text(response)

            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                if self.verbose:
                    print(f"  -> {block.name}({json.dumps(block.input)})")
                result = execute_tool(block.name, block.input)
                if self.verbose:
                    preview = result if len(result) <= 300 else result[:300] + "..."
                    print(f"     {preview}")
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    }
                )
            self.messages.append({"role": "user", "content": tool_results})

        return "Stopped: reached max_turns without a final answer."

    @staticmethod
    def _extract_text(response) -> str:
        texts = [block.text for block in response.content if block.type == "text"]
        return "\n".join(texts).strip()
