from __future__ import annotations

import pytest
import typer

from agentcli_core import AgentFriendlyGroup, HELP_OPTION_NAMES


def _make_app() -> typer.Typer:
    app = typer.Typer(
        cls=AgentFriendlyGroup,
        add_completion=False,
        no_args_is_help=True,
        context_settings=HELP_OPTION_NAMES,
        rich_markup_mode=None,
        suggest_commands=False,
    )

    @app.command("ok")
    def ok() -> None:
        print("ok")

    @app.command("other")
    def other() -> None:
        print("other")

    return app


def test_invalid_command_prints_error_then_relevant_help(capsys: pytest.CaptureFixture[str]) -> None:
    app = _make_app()

    with pytest.raises(SystemExit) as exc_info:
        app(args=["missing"], prog_name="tool")

    captured = capsys.readouterr()
    assert exc_info.value.code == 2
    assert captured.err.startswith("Error: No such command 'missing'.\n\n")
    assert "Usage:" in captured.err
    assert "Commands:" in captured.err
    assert "ok" in captured.err


def test_no_args_is_help_exits_successfully(capsys: pytest.CaptureFixture[str]) -> None:
    app = _make_app()

    with pytest.raises(SystemExit) as exc_info:
        app(args=[], prog_name="tool")

    captured = capsys.readouterr()
    assert exc_info.value.code == 0
    assert "Usage:" in captured.out
    assert "Commands:" in captured.out
