from __future__ import annotations

from agentcli_core.cookies import cookie_header_from_mapping, parse_cookie_header


def test_parse_cookie_header_ignores_malformed_parts() -> None:
    assert parse_cookie_header("a=1; bad; b = two=2 ; =skip") == {"a": "1", "b": "two=2"}


def test_cookie_header_from_mapping() -> None:
    assert cookie_header_from_mapping({"a": "1", "b": "2"}) == "a=1; b=2"
