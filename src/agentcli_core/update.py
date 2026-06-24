from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable, Sequence
from typing import NoReturn

Echo = Callable[[str], None]


def _print_stderr(message: str) -> None:
    print(message, file=sys.stderr)


def uv_tool_update_command(source: str, *, reinstall: bool = True, extra_args: Sequence[str] = ()) -> tuple[str, ...]:
    command = ["uv", "tool", "install"]
    if reinstall:
        command.append("--reinstall")
    command.extend(extra_args)
    command.append(source)
    return tuple(command)


def run_uv_tool_update(
    source: str,
    *,
    reinstall: bool = True,
    extra_args: Sequence[str] = (),
    echo: Echo = print,
    err_echo: Echo = _print_stderr,
) -> int:
    """Run `uv tool install` update and return the subprocess exit code."""

    command = uv_tool_update_command(source, reinstall=reinstall, extra_args=extra_args)
    echo(f"Running: {' '.join(command)}")
    try:
        result = subprocess.run(command, check=False)
    except FileNotFoundError:
        err_echo("Update failed: uv is not installed or not available in PATH.")
        err_echo("Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh")
        return 1
    except OSError as exc:
        err_echo(f"Update failed: {exc}")
        return 1
    return int(result.returncode)


def run_uv_tool_update_or_exit(
    source: str,
    *,
    reinstall: bool = True,
    extra_args: Sequence[str] = (),
    echo: Echo = print,
    err_echo: Echo = _print_stderr,
) -> NoReturn:
    code = run_uv_tool_update(
        source,
        reinstall=reinstall,
        extra_args=extra_args,
        echo=echo,
        err_echo=err_echo,
    )
    raise SystemExit(code)
