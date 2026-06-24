from __future__ import annotations


def normalize_block(text: str) -> str:
    """Trim outer blank lines while preserving internal indentation."""

    return text.strip("\n")


def extract_help_section(text: str, heading: str) -> str | None:
    """Extract a simple titled help section from a plain-text help block.

    Sections are headings ending in `:` followed by indented lines. Extraction
    stops at the next non-indented heading line.
    """

    wanted = heading.rstrip(":") + ":"
    lines = text.splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        if line.strip() == wanted:
            start = index
            break
    if start is None:
        return None

    end = len(lines)
    for index in range(start + 1, len(lines)):
        line = lines[index]
        stripped = line.strip()
        if stripped and not line.startswith((" ", "\t")) and stripped.endswith(":"):
            end = index
            break
    return "\n".join(lines[start:end]).rstrip()


def format_safe_examples(examples: list[str], *, heading: str = "Examples") -> str:
    body = "\n".join(f"  {example}" for example in examples)
    return f"{heading}:\n{body}" if body else f"{heading}:"
