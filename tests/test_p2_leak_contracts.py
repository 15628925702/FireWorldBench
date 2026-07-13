from __future__ import annotations

from fireworldbench import schema_validation  # noqa: F401
from scripts.opaque_id_p2_leak_001 import make_opaque_id, scan_public_payload


def test_opaque_id_is_stable_without_exposing_private_key() -> None:
    value = make_opaque_id("v1", "T1-A", "dev_id", "test-only-private-key", "D01/70U01")
    assert value == make_opaque_id("v1", "T1-A", "dev_id", "test-only-private-key", "D01/70U01")
    assert value.startswith("FWB-v1-T1-A-dev_id-")
    assert "70U01" not in value


def test_public_payload_passes_when_opaque() -> None:
    payload = {"sample_id": "FWB-v1-T1-A-dev_id-0123456789abcdef", "answer": {"label": "insufficient_information"}}
    assert scan_public_payload(payload) == []


def test_public_payload_rejects_private_and_raw_source_tokens() -> None:
    payload = {
        "sample_id": "FWB-v1-T1-A-dev_id-0123456789abcdef",
        "gold": {"label": "fire_forming"},
        "source_case_key": "70U01",
        "ref": "C:\\private\\Immersed-Tunnel-CFD\\70U01_devc.csv",
    }
    errors = scan_public_payload(payload)
    assert any("forbidden private field" in error for error in errors)
    assert any("raw source answer token" in error for error in errors)
