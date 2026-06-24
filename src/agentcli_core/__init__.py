from __future__ import annotations

from .auth_bundle import AuthBundleSpec, AuthEntry, decode_auth_bundle, encode_auth_bundle
from .cli_app import AgentFriendlyGroup, HELP_OPTION_NAMES, UnknownAsArgsGroup, agent_typer
from .clipboard import clipboard_tool_hint, copy_to_clipboard, read_from_clipboard
from .cookies import cookie_header_from_mapping, parse_cookie_header
from .errors import fail, print_error_with_help
from .output import DEFAULT_OUTPUT_LINE_LIMIT, SpooledOutput, emit_or_spool
from .secrets import ensure_private_dir, read_json_object, unique_paths, write_secret_json, write_secret_text

__all__ = [
    "AgentFriendlyGroup",
    "DEFAULT_OUTPUT_LINE_LIMIT",
    "AuthBundleSpec",
    "AuthEntry",
    "HELP_OPTION_NAMES",
    "SpooledOutput",
    "UnknownAsArgsGroup",
    "agent_typer",
    "clipboard_tool_hint",
    "cookie_header_from_mapping",
    "copy_to_clipboard",
    "decode_auth_bundle",
    "encode_auth_bundle",
    "emit_or_spool",
    "ensure_private_dir",
    "fail",
    "parse_cookie_header",
    "print_error_with_help",
    "read_from_clipboard",
    "read_json_object",
    "unique_paths",
    "write_secret_json",
    "write_secret_text",
]
