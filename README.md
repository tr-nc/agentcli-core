# agentcli-core

Shared infrastructure for Python CLIs that are primarily operated by coding agents.

This is intentionally not a general CLI framework. It provides small, mechanical building blocks that should behave the same across tools:

- Typer/Click app defaults for agent-friendly help and usage errors
- `uv tool install --reinstall ...` self-update helpers
- secure local secret/config file reads and writes
- portable compressed auth bundles
- cross-platform clipboard copy/paste helpers
- small help/error formatting helpers

Business logic stays in each CLI.

## Agent-facing CLI contract

Tools using this package should follow these conventions:

- stdout is for successful machine-consumable output or concise success text.
- stderr is for parse errors, auth/setup hints, warnings, and recovery commands.
- usage errors should print the parse failure first, then relevant help.
- examples should use fake/safe IDs and paths.
- secret files should be written under private directories with best-effort `0700` directory and `0600` file permissions.
- auth export/import should use explicit schema strings and bundle prefixes.

## Example

```python
import typer
from agentcli_core import AgentFriendlyGroup, HELP_OPTION_NAMES
from agentcli_core.update import run_uv_tool_update_or_exit

app = typer.Typer(
    cls=AgentFriendlyGroup,
    add_completion=False,
    no_args_is_help=True,
    context_settings=HELP_OPTION_NAMES,
    rich_markup_mode=None,
    suggest_commands=False,
)

@app.command("update")
def update() -> None:
    run_uv_tool_update_or_exit("git+ssh://git@example.com/org/tool.git")
```
