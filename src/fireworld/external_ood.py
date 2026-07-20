"""Fail-closed manifest and candidate-event builders for external OOD sources."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


TRANSFORM_VERSION = "external-ood-ingest-0.1.0"
IMMERSION_SOURCE_URL = "https://github.com/babeteax/Immersed-Tunnel-Fire-Location-Detection-Data"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def opaque_id(prefix: str, value: str) -> str:
    return f"{prefix}-{hashlib.sha256(value.encode('utf-8')).hexdigest()[:12].upper()}"


def read_csv_metadata(path: Path) -> dict[str, Any]:
    """Verify the source's two-row FDS device CSV header and a monotonic time axis."""
    with path.open(encoding="utf-8", errors="strict", newline="") as handle:
        rows = csv.reader(handle)
        units = next(rows, None)
        names = next(rows, None)
        if units is None or names is None or not names or names[0] != "Time":
            raise ValueError("expected a two-row FDS device CSV header with Time as first field")
        if len(units) != len(names) or len(names) < 2:
            raise ValueError("CSV header rows are inconsistent or contain no measurements")
        first_time: float | None = None
        last_time: float | None = None
        row_count = 0
        for row in rows:
            if len(row) != len(names):
                raise ValueError(f"CSV row {row_count + 3} has an unexpected field count")
            value = float(row[0])
            if last_time is not None and value <= last_time:
                raise ValueError("time axis must be strictly increasing")
            first_time = value if first_time is None else first_time
            last_time = value
            row_count += 1
    if first_time is None or last_time is None or row_count < 2:
        raise ValueError("CSV needs at least two measurements")
    return {
        "row_count": row_count,
        "start_s": first_time,
        "end_s": last_time,
        "sample_interval_s": (last_time - first_time) / (row_count - 1),
        "variable_count": len(names) - 1,
        "variables": names[1:],
        "units": units[1:],
    }


def build_immersed_tunnel_candidates(raw_root: Path, output_root: Path) -> dict[str, int]:
    """Write only provenance manifests, derived metadata, and non-publishable Events.

    No filename-derived source, exhaust, fire, stage, or other QA label is emitted.
    The mapping from raw cases to task labels is intentionally outside this builder.
    """
    csv_root = raw_root / "immersed_tunnel_mirror" / "CFD-Data"
    mirror_root = csv_root.parent
    try:
        source_commit = subprocess.check_output(
            ["git", "-C", str(mirror_root), "rev-parse", "HEAD"], text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        source_commit = "unavailable"
    source_files = sorted(csv_root.glob("*.csv"))
    if not source_files:
        raise FileNotFoundError(f"no CFD CSV files found under {csv_root}")

    manifest_dir = output_root / "source_manifests"
    event_dir = output_root / "events" / "immersed_tunnel"
    derived_dir = output_root / "derived" / "S" / "immersed_tunnel"
    report_dir = output_root / "reports" / "immersed_tunnel"
    for directory in (manifest_dir, event_dir, derived_dir, report_dir):
        directory.mkdir(parents=True, exist_ok=True)

    created_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    manifest_files: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []

    for index, source_file in enumerate(source_files, start=1):
        source_hash = sha256_file(source_file)
        opaque_ref = f"immersed-cfd-{index:04d}"
        try:
            metadata = read_csv_metadata(source_file)
        except (OSError, UnicodeError, ValueError) as error:
            failures.append({"opaque_ref": opaque_ref, "reason": str(error)})
            continue

        event_id = opaque_id("FWE", source_hash)
        group_id = opaque_id("FWG", source_hash)
        metadata_path = derived_dir / f"{event_id}.json"
        public_metadata = {
            "schema_version": "external-ood-structured-metadata-0.1.0",
            "event_id": event_id,
            "opaque_source_ref": opaque_ref,
            "time_axis": {
                "start_s": metadata["start_s"],
                "end_s": metadata["end_s"],
                "sample_interval_s": metadata["sample_interval_s"],
                "row_count": metadata["row_count"],
            },
            "variables": metadata["variables"],
            "units": metadata["units"],
            "raw_sha256": source_hash,
        }
        metadata_path.write_text(json.dumps(public_metadata, indent=2) + "\n", encoding="utf-8")
        event = {
            "schema_version": "2.0.0",
            "event_id": event_id,
            "event_group": group_id,
            "source_domain": "immersed_tunnel",
            "status": "candidate",
            "geometry": {
                "scene_type": "tunnel",
                "coordinate_system": "unknown_source_coordinate_system",
                "dimensions_m": None,
                "regions": [],
            },
            "controls": None,
            "timeline": {
                "start_s": metadata["start_s"],
                "end_s": metadata["end_s"],
                "sample_interval_s": metadata["sample_interval_s"],
            },
            "observations": {
                "structured": {
                    "ref": str(metadata_path.relative_to(output_root)),
                    "format": "json",
                    "variables": metadata["variables"],
                    "units_normalized": False,
                },
                "images": None,
                "video": None,
            },
            "ground_truth": {"labels": []},
            "provenance": {
                "source_version": f"git:{source_commit}; label-mapping-not-yet-approved",
                "source_files": [{"opaque_ref": opaque_ref, "sha256": source_hash}],
                "transform_version": TRANSFORM_VERSION,
                "created_at": created_at,
                "fds": None,
            },
            "license": {
                "license_id": None,
                "evidence_ref": None,
                "citation": "Immersed Tunnel Fire Detection Data Set repository mirror; license verification pending.",
                "allowed_uses": ["research", "evaluation"],
                "redistribution": "unknown",
            },
        }
        (event_dir / f"{event_id}.json").write_text(json.dumps(event, indent=2) + "\n", encoding="utf-8")
        manifest_files.append(
            {
                "opaque_ref": opaque_ref,
                "sha256": source_hash,
                "bytes": source_file.stat().st_size,
                "asset_type": "fds_device_csv",
                "parsed": True,
                "row_count": metadata["row_count"],
                "variable_count": metadata["variable_count"],
            }
        )
        candidates.append({"event_id": event_id, "event_group": group_id, "opaque_ref": opaque_ref})

    manifest = {
        "schema_version": "external-ood-source-manifest-0.1.0",
        "source_domain": "immersed_tunnel",
        "official_url": IMMERSION_SOURCE_URL,
        "source_version": f"git:{source_commit}",
        "acquisition_status": "local_raw_preexisting",
        "created_at": created_at,
        "raw_root": "raw/immersed_tunnel",
        "license_status": "unverified",
        "asset_types": ["fds_device_csv"],
        "original_label_fields": [],
        "files": manifest_files,
        "failures": failures,
        "candidate_events": candidates,
        "formal_event_count": 0,
        "formal_qa_count": 0,
        "publication_gate": "blocked_pending_license_and_documented_case_mapping",
    }
    manifest_path = manifest_dir / "immersed_tunnel.source_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    report = {
        "source_domain": "immersed_tunnel",
        "status": "not_accepted",
        "raw_files": len(source_files),
        "parsed_files": len(manifest_files),
        "candidate_events": len(candidates),
        "formal_qualified_events": 0,
        "formal_qa": 0,
        "failed_or_quarantined": len(failures),
        "hard_gates": [
            "license evidence not verified",
            "case-to-control mapping not documented and approved",
            "no source-grounded task labels or QA built",
            "group split, shortcut, and source-level acceptance not run",
        ],
        "source_manifest_sha256": sha256_file(manifest_path),
    }
    (report_dir / "candidate_ingest_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return {"raw_files": len(source_files), "parsed": len(manifest_files), "candidates": len(candidates), "failures": len(failures)}


def build_furg_candidate_split(raw_root: Path, output_root: Path) -> dict[str, int]:
    """Freeze video-level groups before any FURG frame/clip derivative is made.

    FURG stays a separately reported substitute and no QA is generated here.
    """
    source_root = raw_root / "furg_fire_substitute"
    videos = sorted(source_root.glob("*.mp4"))
    if not videos:
        raise FileNotFoundError(f"no FURG videos found under {source_root}")
    xml_by_stem = {path.stem.casefold(): path for path in source_root.glob("*.xml")}
    groups = []
    missing_xml = 0
    for index, video in enumerate(videos, start=1):
        xml = xml_by_stem.get(video.stem.casefold())
        if xml is None:
            missing_xml += 1
        video_hash = sha256_file(video)
        groups.append({
            "event_group": opaque_id("FWG", video_hash),
            "opaque_video_ref": f"furg-video-{index:03d}",
            "video_sha256": video_hash,
            "xml_sha256": sha256_file(xml) if xml is not None else None,
            "split": "real_video_ood",
            "derivative_policy": "all frames, clips, and image derivatives remain in this event_group and split",
        })
    split_dir = output_root / "splits"
    report_dir = output_root / "reports" / "furg_fire_substitute"
    split_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    split_path = split_dir / "furg_fire_substitute_candidate_groups.json"
    split_path.write_text(json.dumps({
        "schema_version": "external-ood-candidate-split-0.1.0",
        "source_domain": "furg_fire_substitute",
        "role": "Real-Video-OOD-Substitute",
        "status": "candidate_only_not_release",
        "split": "real_video_ood",
        "groups": groups,
    }, indent=2) + "\n", encoding="utf-8")
    report_path = report_dir / "candidate_split_report.json"
    report_path.write_text(json.dumps({
        "source_domain": "furg_fire_substitute",
        "status": "not_accepted",
        "video_groups": len(groups),
        "cross_split_group_leakage": 0,
        "missing_xml": missing_xml,
        "formal_qualified_events": 0,
        "formal_qa": 0,
        "hard_gates": ["derived clips/assets not yet built", "XML no-box semantics not confirmed", "task-specific QA eligibility not accepted", "external license confirmation deferred"],
        "split_manifest_sha256": sha256_file(split_path),
    }, indent=2) + "\n", encoding="utf-8")
    return {"video_groups": len(groups), "missing_xml": missing_xml, "formal_events": 0, "formal_qa": 0}


def main() -> int:
    parser = argparse.ArgumentParser(description="Build fail-closed external OOD source artifacts")
    parser.add_argument("--source", choices=("immersed_tunnel", "furg_split"), required=True)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    result = (
        build_immersed_tunnel_candidates(args.raw_root, args.output_root)
        if args.source == "immersed_tunnel"
        else build_furg_candidate_split(args.raw_root, args.output_root)
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
