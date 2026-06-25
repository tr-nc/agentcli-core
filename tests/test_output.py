from __future__ import annotations

import json
import re
import sys
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


def test_emit_or_spool_can_emit_json_spool_pointer(capsys) -> None:
    text = json.dumps({"items": [1, 2, 3]}, indent=2)
    path = emit_or_spool(
        text,
        line_limit=2,
        label="stdout",
        content_type="json-auto",
    )

    captured = capsys.readouterr()
    assert path is not None
    assert path.read_text(encoding="utf-8") == text
    payload = json.loads(captured.out)
    assert payload["kind"] == "spooled-output"
    assert payload["label"] == "stdout"
    assert payload["truncated"] is True
    assert payload["full_output"] == path.resolve().as_uri()


def test_emit_or_spool_json_auto_falls_back_for_non_json(capsys) -> None:
    path = emit_or_spool("a\nb\nc\n", line_limit=2, content_type="json-auto")

    captured = capsys.readouterr()
    assert path is not None
    assert "output omitted: 3 lines exceed the 2-line inline limit" in captured.out


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


def test_spooled_output_can_disable_when_stdout_redirected(monkeypatch, tmp_path) -> None:
    output_path = tmp_path / "out.txt"
    original_stdout = sys.stdout
    with output_path.open("w", encoding="utf-8") as file:
        monkeypatch.setattr(sys, "stdout", file)
        with SpooledOutput(line_limit=1, disable_on_redirect=True):
            print("one")
            print("two")
    monkeypatch.setattr(sys, "stdout", original_stdout)

    assert output_path.read_text(encoding="utf-8") == "one\ntwo\n"
