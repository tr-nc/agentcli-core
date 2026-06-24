from __future__ import annotations

import stat

from agentcli_core.secrets import read_json_object, write_secret_json, write_secret_text


def test_write_secret_json_roundtrip(tmp_path) -> None:
    path = tmp_path / "private" / "config.json"
    write_secret_json(path, {"token": "secret"})

    assert read_json_object(path) == {"token": "secret"}
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_write_secret_text_roundtrip(tmp_path) -> None:
    path = tmp_path / "private" / "token"
    write_secret_text(path, "secret")

    assert path.read_text(encoding="utf-8") == "secret"
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
