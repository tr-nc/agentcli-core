from __future__ import annotations

import os
import shutil
import subprocess
import sys


def run_clipboard_command(command: list[str], *, input_text: str | None = None) -> str | None:
    try:
        proc = subprocess.run(
            command,
            input=input_text,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except (FileNotFoundError, OSError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout


def copy_to_clipboard(text: str) -> bool:
    if sys.platform == "darwin":
        return run_clipboard_command(["pbcopy"], input_text=text) is not None
    if os.name == "nt":
        return run_clipboard_command(["clip"], input_text=text) is not None

    commands = (
        ["wl-copy"],
        ["xclip", "-selection", "clipboard"],
        ["xsel", "--clipboard", "--input"],
    )
    return any(run_clipboard_command(list(command), input_text=text) is not None for command in commands)


def read_from_clipboard() -> str | None:
    if sys.platform == "darwin":
        return run_clipboard_command(["pbpaste"])
    if os.name == "nt":
        return run_clipboard_command(["powershell", "-NoProfile", "-Command", "Get-Clipboard"])

    commands = (
        ["wl-paste"],
        ["xclip", "-selection", "clipboard", "-out"],
        ["xsel", "--clipboard", "--output"],
    )
    for command in commands:
        output = run_clipboard_command(list(command))
        if output:
            return output
    return None


def clipboard_tool_hint() -> str:
    if sys.platform == "darwin":
        return "pbcopy/pbpaste"
    if os.name == "nt":
        return "clip/Get-Clipboard"

    candidates = ["wl-copy/wl-paste", "xclip", "xsel"]
    missing = [candidate for candidate in candidates if not shutil.which(candidate.split("/")[0])]
    if len(missing) == len(candidates):
        return "install wl-clipboard, xclip, or xsel, or use --stdout / paste -"
    return "system clipboard"
