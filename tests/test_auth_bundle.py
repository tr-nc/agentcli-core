from __future__ import annotations

import json

from agentcli_core.auth_bundle import AuthBundleSpec, AuthEntry, auth_bundle_entries, decode_auth_bundle, encode_auth_bundle


SPEC = AuthBundleSpec(
    schema="tool.auth-bundle.v1",
    prefix="tool-auth-v1:",
    begin_marker="-----BEGIN TOOL AUTH BUNDLE-----",
    end_marker="-----END TOOL AUTH BUNDLE-----",
    label="tool auth bundle",
)


def test_auth_bundle_roundtrip() -> None:
    bundle = encode_auth_bundle(
        [AuthEntry(scope="api", kind="token", data={"token": "secret"}, source="test")],
        spec=SPEC,
    )

    payload = decode_auth_bundle(bundle, spec=SPEC)
    entries = auth_bundle_entries(payload)

    assert payload["schema"] == SPEC.schema
    assert entries == [
        {
            "scope": "api",
            "kind": "token",
            "data": {"token": "secret"},
            "source": "test",
        }
    ]


def test_decode_accepts_raw_json() -> None:
    raw = json.dumps({"schema": SPEC.schema, "entries": []})
    assert decode_auth_bundle(raw, spec=SPEC)["entries"] == []
