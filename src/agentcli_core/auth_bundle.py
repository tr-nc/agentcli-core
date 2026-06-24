from __future__ import annotations

import base64
import json
import zlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class AuthEntry:
    scope: str
    kind: str
    data: dict[str, Any]
    source: str

    def to_json(self) -> dict[str, Any]:
        return {
            "scope": self.scope,
            "kind": self.kind,
            "data": self.data,
            "source": self.source,
        }


@dataclass(frozen=True)
class AuthBundleSpec:
    schema: str
    prefix: str
    begin_marker: str
    end_marker: str
    label: str = "auth bundle"


def _entry_to_json(entry: AuthEntry | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(entry, AuthEntry):
        return entry.to_json()
    return dict(entry)


def auth_bundle_payload(entries: Iterable[AuthEntry | Mapping[str, Any]], *, spec: AuthBundleSpec) -> dict[str, Any]:
    return {
        "schema": spec.schema,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "entries": [_entry_to_json(entry) for entry in entries],
    }


def encode_auth_bundle(entries: Iterable[AuthEntry | Mapping[str, Any]], *, spec: AuthBundleSpec) -> str:
    """Encode entries as a portable compressed auth bundle."""

    payload = auth_bundle_payload(entries, spec=spec)
    raw_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    compressed = zlib.compress(raw_json, level=9)
    encoded = base64.urlsafe_b64encode(compressed).decode("ascii")
    return f"{spec.begin_marker}\n{spec.prefix}{encoded}\n{spec.end_marker}\n"


def extract_encoded_auth_bundle(text: str, *, spec: AuthBundleSpec) -> str:
    stripped = text.strip()
    if spec.begin_marker in stripped:
        after_begin = stripped.split(spec.begin_marker, 1)[1]
        before_end = after_begin.split(spec.end_marker, 1)[0]
        stripped = before_end.strip()

    for line in stripped.splitlines():
        line = line.strip()
        if line.startswith(spec.prefix):
            return line[len(spec.prefix) :].strip()

    if stripped.startswith(spec.prefix):
        return stripped[len(spec.prefix) :].strip()

    raise ValueError(f"input does not look like a {spec.label}")


def decode_auth_bundle(text: str, *, spec: AuthBundleSpec, allow_json: bool = True) -> dict[str, Any]:
    """Decode and validate an auth bundle payload.

    If `allow_json` is true, raw JSON payloads are accepted for developer
    convenience and migration tests.
    """

    stripped = text.strip()
    if allow_json and stripped.startswith("{"):
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ValueError(f"failed to decode {spec.label}") from exc
    else:
        encoded = extract_encoded_auth_bundle(text, spec=spec)
        try:
            compressed = base64.urlsafe_b64decode(encoded.encode("ascii"))
            raw_json = zlib.decompress(compressed)
            payload = json.loads(raw_json.decode("utf-8"))
        except Exception as exc:  # noqa: BLE001 - report a stable message to callers.
            raise ValueError(f"failed to decode {spec.label}") from exc

    if not isinstance(payload, dict) or payload.get("schema") != spec.schema:
        raise ValueError(f"unsupported {spec.label} schema")
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise ValueError(f"{spec.label} is missing entries")
    return payload


def auth_bundle_entries(payload: dict[str, Any]) -> list[dict[str, Any]]:
    entries = payload.get("entries")
    if not isinstance(entries, list):
        return []
    return [entry for entry in entries if isinstance(entry, dict)]
