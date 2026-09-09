# Agentic AI - Task Automation Agent

A minimal, dependency-light agent built directly on the Claude API (no
LangChain/CrewAI/etc.) that can automate tasks involving files, HTTP APIs,
and (optionally) shell commands. You give it a task in plain English; it
plans and executes the tool calls needed to complete it.

## How it works

This is the standard "agentic loop":

1. Your task is sent to Claude along with the list of available tools.
2. If Claude answers directly, you're done.
3. If Claude asks to call a tool (e.g. `write_file`), the agent runs that
   Python function locally and sends the result back to Claude.
4. Repeat until Claude gives a final answer or `max_turns` is hit.

```
agentic_ai/
├── agent.py              # the loop itself (model-agnostic-ish, Claude API specifics here)
├── config.py              # loads .env, checks for API key
├── main.py                 # CLI: single task or interactive mode
├── tools/
│   ├── registry.py         # @tool decorator + schema/execution plumbing
│   ├── file_tools.py       # read_file / write_file / list_directory (sandboxed)
│   ├── http_tools.py       # http_request (call any API)
│   └── shell_tools.py      # run_shell_command (off by default)
└── workflows/
    └── example_workflow.py # scripted example: HTTP fetch -> file write
```

## Setup

```bash
cd agentic_ai
python -m venv venv && source venv/bin/activate   # optional but recommended
pip install -r requirements.txt
cp .env.example .env   # then edit .env and add your ANTHROPIC_API_KEY
```

Get an API key at https://console.anthropic.com/

## Usage

Single task:

```bash
python main.py "List the files in the workspace, then create a file called notes.md summarizing what's there"
```

Interactive mode:

```bash
python main.py
task> fetch https://api.github.com/repos/anthropics/anthropic-sdk-python and save the description to repo.txt
task> exit
```

Scripted example workflow (HTTP call chained into a file write):

```bash
python -m workflows.example_workflow
```

## Tools included

| Tool | What it does | Notes |
|---|---|---|
| `read_file` | Read a text file | Sandboxed to `AGENT_WORKDIR` (default `./workspace`) |
| `write_file` | Write/overwrite a text file | Same sandbox; creates parent folders |
| `list_directory` | List a directory's contents | Same sandbox |
| `http_request` | GET/POST/PUT/PATCH/DELETE any URL | Response body truncated to 6000 chars |
| `run_shell_command` | Run a shell command | **Disabled by default** - see below |

### Enabling shell access

`run_shell_command` gives the agent real command-line access on your
machine, so it's opt-in only:

```bash
export AGENT_ALLOW_SHELL=1
```

Only enable this if you trust the tasks you're giving the agent - a
task-automation agent with shell access can do anything your user account
can do.

### The file sandbox

`read_file` / `write_file` / `list_directory` all resolve paths relative to
`AGENT_WORKDIR` (default: `./workspace`, created automatically) and reject
any path that would escape it (e.g. `../../etc/passwd`). Point
`AGENT_WORKDIR` at a real project directory once you trust a given
workflow.

## Adding a new tool

Tools are self-registering, so adding one is just a new function:

```python
# tools/my_tools.py
from tools.registry import tool

@tool(
    name="send_slack_message",
    description="Post a message to a Slack channel via webhook.",
    input_schema={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Message text to send"},
        },
        "required": ["text"],
    },
)
def send_slack_message(text: str) -> str:
    # your implementation here
    return "sent"
```

Then import the module once (so the decorator runs) near the other tool
imports at the top of `agent.py`:

```python
import tools.my_tools  # noqa: F401
```

That's it - Claude will see the new tool on the next run and can call it
whenever the task calls for it.

## Configuration (env vars)

| Variable | Default | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | *(required)* | Your Claude API key |
| `AGENT_MODEL` | `claude-sonnet-5` | Model to use |
| `AGENT_WORKDIR` | `./workspace` | Sandbox root for file tools |
| `AGENT_ALLOW_SHELL` | `0` | Set to `1` to enable `run_shell_command` |

## Safety notes

- File tools are sandboxed; shell access is opt-in and off by default.
- The agent stops after `max_turns` (default 15) even if it hasn't
  finished, so it can't loop forever burning API credits.
- `write_file` overwrites existing files without asking - back up
  anything important in `AGENT_WORKDIR` before pointing the agent at a
  real project.
- There's no human-confirmation step before tool calls execute. For
  higher-stakes automation, add a confirmation prompt in `agent.py`'s
  tool-execution loop before calling `execute_tool` for sensitive tools.
