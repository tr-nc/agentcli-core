from __future__ import annotations

import re
from pathlib import Path

from agentcli_core.output import SpooledOutput, emit_or_spool


def test_emit_or_spool_keeps_small_output_inline(capsys) -> None:
    path = emit_or_spool("a\nb\n", line_limit=2)

    captured = capsys.readouterr()
    assert path is None
    assert captured.out == "a\nb\n"


def test_emit_or_spool_writes_large_output_to_temp_file(capsys) -> None:
    path = emit_or_spool("a\nb\nc\n", line_limit=2, label="stdout")

    captured = capsys.readouterr()
    assert path is not None
    assert path.read_text(encoding="utf-8") == "a\nb\nc\n"
    assert "stdout omitted: 3 lines exceed the 2-line inline limit" in captured.out
    assert f"read with: cat {path}" in captured.out


def test_spooled_output_captures_and_spools_stdout(capsys) -> None:
    with SpooledOutput(line_limit=2):
        print("one")
        print("two")
        print("three")

    captured = capsys.readouterr()
    match = re.search(r"read with: cat (.+)", captured.out)
    assert match is not None
    path = Path(match.group(1).strip())
    assert path.read_text(encoding="utf-8") == "one\ntwo\nthree\n"


def test_spooled_output_replays_small_output(capsys) -> None:
    with SpooledOutput(line_limit=3):
        print("one")
        print("two")

    captured = capsys.readouterr()
    assert captured.out == "one\ntwo\n"
