from __future__ import annotations

from typing import NoReturn

import click
import typer


def print_error_with_help(exc: click.ClickException, *, prefix: str = "Error") -> None:
    """Print a Click exception followed by the relevant command help.

    The parse failure is deliberately first so an agent can see what went wrong
    before scanning the grammar/help block.
    """

    click.echo(f"{prefix}: {exc.format_message()}", err=True)
    ctx = getattr(exc, "ctx", None)
    if ctx is None:
        return
    click.echo("", err=True)
    click.echo(ctx.get_help(), err=True)


def fail(message: str, *, code: int = 1, help_text: str | None = None) -> NoReturn:
    """Print an error to stderr and exit from a Typer command."""

    typer.echo(message, err=True)
    if help_text:
        typer.echo("", err=True)
        typer.echo(help_text, err=True)
    raise typer.Exit(code)
