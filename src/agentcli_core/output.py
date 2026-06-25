from __future__ import annotations

import io
import json
import os
import stat
import sys
import tempfile
from pathlib import Path
from types import TracebackType
from typing import Literal, TextIO, cast

DEFAULT_OUTPUT_LINE_LIMIT = 500
OutputContentType = Literal["text", "json", "json-auto"]


def _line_count(text: str) -> int:
    if not text:
        return 0
    return len(text.splitlines())


def _file_url(path: Path) -> str:
    return path.resolve().as_uri()


def _spool_notice(*, label: str, line_count: int, line_limit: int, path: Path) -> str:
    return (
        f"{label} omitted: {line_count} lines exceed the {line_limit}-line inline limit.\n"
        f"full {label}: {_file_url(path)}\n"
        f"read with: cat {path}\n"
    )


def _json_spool_notice(
    *, label: str, line_count: int, line_limit: int, path: Path
) -> str:
    return json.dumps(
        {
            "kind": "spooled-output",
            "label": label,
            "truncated": True,
            "line_count": line_count,
            "line_limit": line_limit,
            "full_output": _file_url(path),
            "read_with": f"cat {path}",
        },
        indent=2,
        ensure_ascii=False,
        sort_keys=True,
    ) + "\n"


def _is_json_text(text: str) -> bool:
    stripped = text.strip()
    if not stripped or stripped[0] not in "[{":
        return False
    try:
        json.loads(stripped)
    except json.JSONDecodeError:
        return False
    return True


def _should_emit_json_spool_notice(text: str, content_type: OutputContentType) -> bool:
    if content_type == "json":
        return True
    if content_type == "json-auto":
        return _is_json_text(text)
    return False


def _stream_is_regular_file(stream: TextIO) -> bool:
    try:
        return stat.S_ISREG(os.fstat(stream.fileno()).st_mode)
    except (AttributeError, OSError, ValueError):
        return False


def emit_or_spool(
    text: str,
    *,
    stream: TextIO | None = None,
    label: str = "output",
    line_limit: int = DEFAULT_OUTPUT_LINE_LIMIT,
    prefix: str = "agentcli-output-",
    suffix: str = ".txt",
    content_type: OutputContentType = "text",
) -> Path | None:
    """Emit text inline, or write large output to a temp file and emit a pointer.

    When ``content_type`` is ``"json"``, the spool pointer is emitted as a JSON
    object so machine consumers can still parse stdout. ``"json-auto"`` emits a
    JSON pointer only when the complete captured text is valid JSON; otherwise it
    falls back to the normal text notice.

    Returns the temp path when spooled, otherwise None.
    """

    if stream is None:
        stream = sys.stdout

    lines = _line_count(text)
    if lines <= line_limit:
        stream.write(text)
        stream.flush()
        return None

    file_handle = tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        delete=False,
        prefix=prefix,
        suffix=suffix,
    )
    with file_handle:
        file_handle.write(text)
    path = Path(file_handle.name)
    if _should_emit_json_spool_notice(text, content_type):
        stream.write(
            _json_spool_notice(
                label=label,
                line_count=lines,
                line_limit=line_limit,
                path=path,
            )
        )
    else:
        stream.write(
            _spool_notice(
                label=label,
                line_count=lines,
                line_limit=line_limit,
                path=path,
            )
        )
    stream.flush()
    return path


class SpooledOutput:
    """Capture stdout/stderr for a command and spool very large output.

    This is designed for agent-facing CLIs where huge inline output wastes model
    context. Output is replayed at command end if it is below the line limit.
    When it exceeds the limit, only a temp-file pointer is printed.
    """

    def __init__(
        self,
        *,
        line_limit: int = DEFAULT_OUTPUT_LINE_LIMIT,
        enabled: bool = True,
        stdout_label: str = "stdout",
        stderr_label: str = "stderr",
        stdout_content_type: OutputContentType = "text",
        stderr_content_type: OutputContentType = "text",
        disable_on_redirect: bool = False,
    ) -> None:
        self.line_limit = line_limit
        self.enabled = enabled
        self.stdout_label = stdout_label
        self.stderr_label = stderr_label
        self.stdout_content_type = stdout_content_type
        self.stderr_content_type = stderr_content_type
        self.disable_on_redirect = disable_on_redirect
        self._stdout: TextIO | None = None
        self._stderr: TextIO | None = None
        self._stdout_buffer: io.StringIO | None = None
        self._stderr_buffer: io.StringIO | None = None

    def __enter__(self) -> SpooledOutput:
        if not self.enabled:
            return self
        if self.disable_on_redirect and (
            _stream_is_regular_file(sys.stdout) or _stream_is_regular_file(sys.stderr)
        ):
            self.enabled = False
            return self
        self._stdout = sys.stdout
        self._stderr = sys.stderr
        self._stdout_buffer = io.StringIO()
        self._stderr_buffer = io.StringIO()
        sys.stdout = self._stdout_buffer  # type: ignore[assignment]
        sys.stderr = self._stderr_buffer  # type: ignore[assignment]
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        if not self.enabled:
            return False

        stdout = self._stdout if self._stdout is not None else cast(TextIO, sys.__stdout__)
        stderr = self._stderr if self._stderr is not None else cast(TextIO, sys.__stderr__)
        stdout_text = self._stdout_buffer.getvalue() if self._stdout_buffer is not None else ""
        stderr_text = self._stderr_buffer.getvalue() if self._stderr_buffer is not None else ""
        sys.stdout = stdout  # type: ignore[assignment]
        sys.stderr = stderr  # type: ignore[assignment]

        emit_or_spool(
            stdout_text,
            stream=stdout,
            label=self.stdout_label,
            line_limit=self.line_limit,
            prefix="agentcli-stdout-",
            content_type=self.stdout_content_type,
        )
        emit_or_spool(
            stderr_text,
            stream=stderr,
            label=self.stderr_label,
            line_limit=self.line_limit,
            prefix="agentcli-stderr-",
            content_type=self.stderr_content_type,
        )
        return False


def output_spooling_enabled() -> bool:
    return os.environ.get("AGENTCLI_DISABLE_OUTPUT_SPOOL", "").strip().lower() not in {"1", "true", "yes", "on"}


def output_line_limit(default: int = DEFAULT_OUTPUT_LINE_LIMIT) -> int:
    raw = os.environ.get("AGENTCLI_OUTPUT_LINE_LIMIT", "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default
