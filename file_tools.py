"""
File tools, sandboxed to a single workspace directory.

Every path the agent gives us is resolved relative to AGENT_WORKDIR and
checked to make sure it can't escape that directory (no ../.. tricks).
This is the difference between "an agent that automates files" and
"an agent that can overwrite anything on your machine" - keep it.
"""

import os

from tools.registry import tool

BASE_DIR = os.path.abspath(os.environ.get("AGENT_WORKDIR", "./workspace"))
os.makedirs(BASE_DIR, exist_ok=True)


def _safe_path(relative_path: str) -> str:
    full = os.path.abspath(os.path.join(BASE_DIR, relative_path))
    if os.path.commonpath([full, BASE_DIR]) != BASE_DIR:
        raise ValueError(
            f"Path '{relative_path}' resolves outside the workspace directory "
            f"({BASE_DIR}) and was blocked."
        )
    return full


@tool(
    name="read_file",
    description=(
        "Read the full text contents of a file inside the agent's workspace "
        "directory. Path is relative to the workspace root."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Relative path to the file, e.g. 'notes/todo.txt'",
            }
        },
        "required": ["path"],
    },
)
def read_file(path: str) -> str:
    full = _safe_path(path)
    if not os.path.isfile(full):
        return f"Error: file not found: {path}"
    with open(full, "r", encoding="utf-8") as f:
        return f.read()


@tool(
    name="write_file",
    description=(
        "Write text content to a file inside the agent's workspace directory, "
        "creating parent folders and overwriting the file if it already "
        "exists. Path is relative to the workspace root."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Relative path to the file, e.g. 'output/report.md'",
            },
            "content": {
                "type": "string",
                "description": "Text content to write to the file.",
            },
        },
        "required": ["path", "content"],
    },
)
def write_file(path: str, content: str) -> str:
    full = _safe_path(path)
    os.makedirs(os.path.dirname(full) or BASE_DIR, exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Wrote {len(content)} characters to {path}"


@tool(
    name="list_directory",
    description=(
        "List files and folders inside a directory in the agent's workspace. "
        "Use '.' for the workspace root."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Relative directory path, e.g. '.' or 'data'",
            }
        },
        "required": ["path"],
    },
)
def list_directory(path: str = ".") -> str:
    full = _safe_path(path)
    if not os.path.isdir(full):
        return f"Error: directory not found: {path}"
    entries = sorted(os.listdir(full))
    if not entries:
        return "(empty directory)"
    return "\n".join(entries)
