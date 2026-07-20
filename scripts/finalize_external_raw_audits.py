"""Freeze source-manifest and quarantine decisions from raw-only audits."""
from __future__ import annotations
import argparse, hashlib, json
from datetime import UTC, datetime
from pathlib import Path

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def main() -> int:
    p = argparse.ArgumentParser(); p.add_argument("--root", type=Path, required=True); args = p.parse_args(); root = args.root
    reports = root / "external_ood/reports/raw_audit"; manifests = root / "external_ood/source_manifests"; quarantine = root / "external_ood/quarantine"
    manifests.mkdir(parents=True, exist_ok=True); quarantine.mkdir(parents=True, exist_ok=True)
    created = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    for source, report_name, url, license_status, mode in [
        ("polyu", "polyu", "https://www.bse.polyu.edu.hk/PolyUFire/Project.html", "unverified", "raw_only"),
        ("furg_fire_substitute", "furg", "https://github.com/steffensbola/furg-fire-dataset", "CC0-1.0-local-copy", "substitute_only"),
    ]:
        report_path = reports / f"{report_name}_raw_audit.json"
        report = json.loads(report_path.read_text())
        payload = {"schema_version": "external-ood-source-manifest-0.1.0", "source_domain": source, "official_url": url,
            "acquisition_status": "local_raw_preexisting", "created_at": created, "audit_report": str(report_path.relative_to(root)),
            "audit_report_sha256": sha256(report_path), "license_status": license_status, "inclusion_mode": mode,
            "formal_event_count": 0, "formal_qa_count": 0, "acceptance_status": "not_accepted", "raw_audit": report}
        (manifests / f"{source}.source_manifest.json").write_text(json.dumps(payload, indent=2) + "\n")
    wrong = root / "raw/fire360/fire360_mirror"
    record = {"source": "fire360_mirror", "status": "quarantined", "created_at": created,
        "raw_path": str(wrong.relative_to(root)), "reason": "inspected repository is unrelated software/data, not official Fire360 media or annotations",
        "prohibited_claims": ["Fire360", "Real-Video-OOD", "official 228-video corpus"], "raw_deleted": False}
    (quarantine / "fire360_mirror_wrong_source.json").write_text(json.dumps(record, indent=2) + "\n")
    return 0
if __name__ == "__main__": raise SystemExit(main())
