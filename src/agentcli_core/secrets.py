from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, TypeVar

T = TypeVar("T")

SECRET_DIR_MODE = 0o700
SECRET_FILE_MODE = 0o600


def unique_paths(paths: list[Path]) -> list[Path]:
    """Return paths in first-seen order after expanduser string de-duplication."""

    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path.expanduser())
        if key in seen:
            continue
        unique.append(path)
        seen.add(key)
    return unique


def ensure_private_dir(path: Path, *, mode: int = SECRET_DIR_MODE) -> None:
    """Create a directory and apply best-effort private permissions."""

    path.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(path, mode)
    except OSError:
        pass


def chmod_secret(path: Path, *, mode: int = SECRET_FILE_MODE) -> None:
    try:
        os.chmod(path, mode)
    except OSError:
        pass


def read_json_object(path: Path, *, default: T | None = None) -> dict[str, Any] | T | None:
    """Read a JSON object from path.

    Returns `default` when the file is missing, unreadable, invalid JSON, or not
    a JSON object. This matches the forgiving behavior preferred by small agent
    tools whose auth/config may be repaired by rerunning an auth command.
    """

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return default
    return data if isinstance(data, dict) else default


def read_first_json_object(paths: list[Path], *, default: T | None = None) -> dict[str, Any] | T | None:
    for path in unique_paths(paths):
        data = read_json_object(path, default=None)
        if data:
            return data
    return default


def atomic_write_text(path: Path, text: str, *, private: bool = False) -> None:
    ensure_private_dir(path.parent)
    tmp_path = path.with_name(f".{path.name}.tmp")
    tmp_path.write_text(text, encoding="utf-8")
    if private:
        chmod_secret(tmp_path)
    tmp_path.replace(path)
    if private:
        chmod_secret(path)


def write_secret_text(path: Path, text: str) -> None:
    """Atomically write secret text with best-effort 0600 permissions."""

    atomic_write_text(path, text, private=True)


def write_secret_json(path: Path, data: dict[str, Any], *, sort_keys: bool = True) -> None:
    """Atomically write a JSON secret with best-effort 0600 permissions."""

    text = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=sort_keys) + "\n"
    write_secret_text(path, text)
