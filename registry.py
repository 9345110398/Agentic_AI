"""
Simple tool registry.

Any function decorated with @tool(...) becomes callable by the agent.
This keeps tool definitions (JSON schema Claude sees) right next to the
Python function that implements them, so adding a new tool is a
one-function, one-decorator change.
"""

from typing import Any, Callable, Dict

_TOOLS: Dict[str, Dict[str, Any]] = {}


def tool(name: str, description: str, input_schema: Dict[str, Any]) -> Callable:
    """Decorator that registers a function as an agent tool.

    Args:
        name: Tool name Claude will use to call it (must be unique).
        description: Clear description of what the tool does and when to
            use it. Claude decides whether to call the tool based on this,
            so be specific.
        input_schema: JSON Schema (type "object") describing the arguments.
    """

    def decorator(fn: Callable) -> Callable:
        if name in _TOOLS:
            raise ValueError(f"Tool '{name}' is already registered")
        _TOOLS[name] = {
            "name": name,
            "description": description,
            "input_schema": input_schema,
            "handler": fn,
        }
        return fn

    return decorator


def get_tool_schemas() -> list:
    """Return the tool definitions in the shape the Claude API expects."""
    return [
        {
            "name": t["name"],
            "description": t["description"],
            "input_schema": t["input_schema"],
        }
        for t in _TOOLS.values()
    ]


def execute_tool(name: str, tool_input: Dict[str, Any]) -> str:
    """Run a registered tool and return a string result (or error message).

    Errors are caught and returned as text rather than raised, because a
    failed tool call is something Claude should see and react to (e.g. by
    trying a different path), not something that should crash the agent.
    """
    if name not in _TOOLS:
        return f"Error: unknown tool '{name}'"
    try:
        return str(_TOOLS[name]["handler"](**tool_input))
    except Exception as exc:  # noqa: BLE001 - deliberately broad, fed back to the model
        return f"Error executing tool '{name}': {exc}"


def registered_tool_names() -> list:
    return list(_TOOLS.keys())
