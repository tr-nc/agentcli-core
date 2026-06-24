from __future__ import annotations


def parse_cookie_header(cookie_header: str) -> dict[str, str]:
    """Parse a Cookie header into a name/value mapping.

    This intentionally implements the simple CLI use case: split semicolon
    separated `name=value` pairs, ignore malformed parts, preserve raw values.
    """

    cookies: dict[str, str] = {}
    for part in cookie_header.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        key, value = part.split("=", 1)
        key = key.strip()
        if key:
            cookies[key] = value.strip()
    return cookies


def cookie_header_from_mapping(cookies: dict[str, str]) -> str:
    return "; ".join(f"{key}={value}" for key, value in cookies.items() if key)
