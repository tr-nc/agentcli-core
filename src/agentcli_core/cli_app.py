from __future__ import annotations

import sys
from collections.abc import Sequence
from importlib import import_module
from typing import Any

import click
import typer
from typer.core import TyperGroup

from .errors import print_error_with_help

HELP_OPTION_NAMES = {"help_option_names": ["-h", "--help"]}


def _exception_type(module_name: str, name: str) -> type[BaseException] | None:
    try:
        module = import_module(module_name)
    except ModuleNotFoundError:
        return None
    exception_type = getattr(module, name, None)
    return exception_type if isinstance(exception_type, type) else None


def _click_exception_types(name: str) -> tuple[type[BaseException], ...]:
    types: list[type[BaseException]] = []
    for exception_type in (
        getattr(click, name, None),
        getattr(click.exceptions, name, None),
        _exception_type("typer._click.exceptions", name),
    ):
        if isinstance(exception_type, type) and exception_type not in types:
            types.append(exception_type)
    return tuple(types)


_CLICK_EXCEPTION_TYPES = _click_exception_types("ClickException")
_ABORT_TYPES = _click_exception_types("Abort")
_NO_ARGS_IS_HELP_ERROR_TYPES = _click_exception_types("NoArgsIsHelpError")


class AgentFriendlyGroup(TyperGroup):
    """Typer group that makes usage failures useful to coding agents.

    On parse errors it prints:
    1. the exact parse failure
    2. a blank line
    3. the relevant Click/Typer help block

    `NoArgsIsHelpError` is treated as normal help and exits 0, matching
    `no_args_is_help=True` expectations.
    """

    error_prefix = "Error"

    def main(
        self,
        args: Sequence[str] | None = None,
        prog_name: str | None = None,
        complete_var: str | None = None,
        standalone_mode: bool = True,
        windows_expand_args: bool = True,
        **extra: Any,
    ) -> Any:
        if not standalone_mode:
            return super().main(
                args=args,
                prog_name=prog_name,
                complete_var=complete_var,
                standalone_mode=False,
                windows_expand_args=windows_expand_args,
                **extra,
            )

        try:
            result = super().main(
                args=args,
                prog_name=prog_name,
                complete_var=complete_var,
                standalone_mode=False,
                windows_expand_args=windows_expand_args,
                **extra,
            )
        except _CLICK_EXCEPTION_TYPES as exc:
            if isinstance(exc, _NO_ARGS_IS_HELP_ERROR_TYPES) or exc.__class__.__name__ == "NoArgsIsHelpError":
                ctx = getattr(exc, "ctx", None)
                format_message = getattr(exc, "format_message", None)
                fallback = format_message() if callable(format_message) else str(exc)
                click.echo(ctx.get_help() if ctx is not None else fallback)
                sys.exit(0)
            print_error_with_help(exc, prefix=self.error_prefix)
            exit_code = getattr(exc, "exit_code", 2)
            sys.exit(exit_code if isinstance(exit_code, int) else 2)
        except _ABORT_TYPES:
            click.echo("Aborted.", err=True)
            sys.exit(1)

        sys.exit(result if isinstance(result, int) else 0)


class UnknownAsArgsGroup(TyperGroup):
    """Group that treats unknown subcommands as positional args.

    Useful for command grammars such as `tool inspect <id>` while preserving
    explicit subcommands like `tool inspect workflow <id> summary`.
    """

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        if not args and self.no_args_is_help and not ctx.resilient_parsing:
            try:
                from click.exceptions import NoArgsIsHelpError  # type: ignore[attr-defined]
            except ImportError:  # pragma: no cover - old Click fallback.
                NoArgsIsHelpError = click.UsageError  # type: ignore[assignment]
            raise NoArgsIsHelpError(ctx)

        rest = click.core.Command.parse_args(self, ctx, args)

        if getattr(self, "chain", False):
            setattr(ctx, "_protected_args", rest)
            ctx.args = []
            return ctx.args

        if rest:
            first = rest[0]
            if self.get_command(ctx, click.utils.make_str(first)) is None:
                setattr(ctx, "_protected_args", [])
                ctx.args = rest
            else:
                setattr(ctx, "_protected_args", rest[:1])
                ctx.args = rest[1:]

        return ctx.args


def agent_typer(**kwargs: Any) -> typer.Typer:
    """Create a Typer app with defaults shared by agent-facing tools."""

    context_settings = dict(HELP_OPTION_NAMES)
    context_settings.update(kwargs.pop("context_settings", {}) or {})
    kwargs.setdefault("cls", AgentFriendlyGroup)
    kwargs.setdefault("add_completion", False)
    kwargs.setdefault("no_args_is_help", True)
    kwargs.setdefault("rich_markup_mode", None)
    kwargs.setdefault("suggest_commands", False)
    kwargs["context_settings"] = context_settings
    return typer.Typer(**kwargs)
