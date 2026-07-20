"""External raw-audit entry point reserved for the active FireWorld v2 pipeline.

Raw auditing remains separate from Event/QA construction. This module owns future
source-level audit and acceptance work; historical scripts are not release inputs.
"""

from __future__ import annotations

import hashlib
import json
import argparse
from datetime import UTC, datetime
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile
import re
import subprocess


def reports_root(data_root: Path) -> Path:
    """Return the isolated raw-audit report location for an external data root."""
    return data_root / "external_ood" / "reports" / "raw_audit"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def audit_polyu_workbooks(data_root: Path) -> Path:
    """Extract workbook-local field evidence without interpreting rows as labels."""
    workbook_root = data_root / "raw" / "polyu" / "repo" / "2020_TUST_paper"
    namespace = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    workbooks: list[dict[str, object]] = []
    for workbook_path in sorted(workbook_root.glob("*.xlsx")):
        with ZipFile(workbook_path) as archive:
            workbook_xml = ET.fromstring(archive.read("xl/workbook.xml"))
            sheets = [node.attrib["name"] for node in workbook_xml.findall("x:sheets/x:sheet", namespace)]
            shared_strings: list[str] = []
            if "xl/sharedStrings.xml" in archive.namelist():
                shared_xml = ET.fromstring(archive.read("xl/sharedStrings.xml"))
                shared_strings = ["".join(node.itertext()) for node in shared_xml.findall("x:si", namespace)]
            worksheet_name = next(name for name in archive.namelist() if name.startswith("xl/worksheets/sheet"))
            worksheet = ET.fromstring(archive.read(worksheet_name))
            sample_rows: list[list[str]] = []
            for row in worksheet.findall(".//x:row", namespace)[:12]:
                values: list[str] = []
                for cell in row.findall("x:c", namespace):
                    value = cell.findtext("x:v", default="", namespaces=namespace)
                    if cell.attrib.get("t") == "s" and value:
                        values.append(shared_strings[int(value)])
                    else:
                        values.append(value)
                sample_rows.append(values)
        workbooks.append(
            {"file": workbook_path.name, "sha256": _sha256(workbook_path), "bytes": workbook_path.stat().st_size,
             "sheets": sheets, "first_sheet_rows_1_to_12": sample_rows}
        )
    report = {
        "schema_version": "external-ood-raw-audit-0.2.0",
        "source_domain": "polyu",
        "status": "raw_audited_not_accepted",
        "created_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "workbooks": workbooks,
        "formal_events": 0,
        "formal_qa": 0,
        "hard_gates": ["row-level measurement semantics and units require source-aware review", "license evidence not verified", "no source-grounded task rule or split audit"],
    }
    out = reports_root(data_root)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "polyu_raw_audit_v2.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return path


def audit_polyu_database_rows(data_root: Path) -> Path:
    """Inventory database-sheet rows without deciding their physical semantics."""
    workbook_root = data_root / "raw" / "polyu" / "repo" / "2020_TUST_paper"
    namespace = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    result: list[dict[str, object]] = []
    for workbook_path in sorted(workbook_root.glob("*.xlsx")):
        with ZipFile(workbook_path) as archive:
            workbook = ET.fromstring(archive.read("xl/workbook.xml"))
            sheet_nodes = workbook.findall("x:sheets/x:sheet", namespace)
            database_index = next((index + 1 for index, node in enumerate(sheet_nodes) if "database" in node.attrib["name"].casefold()), None)
            if database_index is None:
                result.append({"file": workbook_path.name, "database_sheet": None, "rows": 0, "nonempty_rows": 0, "status": "no_named_database_sheet"})
                continue
            shared: list[str] = []
            if "xl/sharedStrings.xml" in archive.namelist():
                shared_xml = ET.fromstring(archive.read("xl/sharedStrings.xml"))
                shared = ["".join(node.itertext()) for node in shared_xml.findall("x:si", namespace)]
            worksheet = ET.fromstring(archive.read(f"xl/worksheets/sheet{database_index}.xml"))
            rows = worksheet.findall(".//x:row", namespace)
            sampled: list[list[str]] = []
            nonempty = 0
            for row in rows:
                values = []
                for cell in row.findall("x:c", namespace):
                    value = cell.findtext("x:v", default="", namespaces=namespace)
                    values.append(shared[int(value)] if cell.attrib.get("t") == "s" and value else value)
                if any(value.strip() for value in values):
                    nonempty += 1
                    if len(sampled) < 20:
                        sampled.append(values)
            result.append({"file": workbook_path.name, "database_sheet": sheet_nodes[database_index - 1].attrib["name"], "rows": len(rows), "nonempty_rows": nonempty, "first_20_nonempty_rows": sampled, "status": "requires_field_semantic_review"})
    report = {"schema_version": "external-ood-row-audit-0.1.0", "source_domain": "polyu", "status": "candidate_rows_not_events", "database_sheets": result, "formal_events": 0, "formal_qa": 0, "hard_gates": ["do not interpret ranges, missing cells, or cross-study records as truth labels", "unit/scale/field semantic review deferred", "external license confirmation deferred"]}
    out = reports_root(data_root); out.mkdir(parents=True, exist_ok=True); path = out / "polyu_database_row_audit.json"; path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8"); return path


def audit_furg_videos(data_root: Path) -> Path:
    """Audit FURG substitute videos; report assets, never call them Fire360."""
    source_root = data_root / "raw" / "fire360" / "furg_fire_substitute"
    xml_by_stem = {path.stem.casefold(): path for path in source_root.glob("*.xml")}
    videos: list[dict[str, object]] = []
    for video_path in sorted(source_root.glob("*.mp4")):
        xml_path = xml_by_stem.get(video_path.stem.casefold())
        probe = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,codec_name,avg_frame_rate,width,height", "-of", "json", str(video_path)]))
        stream = next(item for item in probe["streams"] if item["codec_type"] == "video")
        annotated = [] if xml_path is None else [int(value) for value in re.findall(r"<frameNumber>(\d+)</frameNumber>", xml_path.read_text(errors="replace"))]
        duration = float(probe["format"]["duration"])
        raw = subprocess.check_output(["ffmpeg", "-v", "error", "-ss", str(duration * 0.1), "-i", str(video_path), "-vf", "fps=1/2,scale=32:32,format=gray", "-frames:v", "5", "-f", "rawvideo", "-"])
        means = [sum(raw[index:index + 1024]) / 1024 for index in range(0, len(raw), 1024) if len(raw[index:index + 1024]) == 1024]
        videos.append({"video_sha256": _sha256(video_path), "bytes": video_path.stat().st_size, "xml_present": xml_path is not None, "xml_sha256": _sha256(xml_path) if xml_path else None, "duration_s": duration, "codec": stream.get("codec_name"), "fps": stream.get("avg_frame_rate"), "width": stream.get("width"), "height": stream.get("height"), "annotated_frames": len(annotated), "annotation_span": [annotated[0], annotated[-1]] if annotated else None, "sample_dynamic": max([abs(a-b) for a, b in zip(means, means[1:])], default=0) > 0.5, "sample_black": bool(means) and max(means) < 2})
    report = {"schema_version": "external-ood-raw-audit-0.2.0", "source_domain": "furg_fire_substitute", "role": "Real-Video-OOD-Substitute", "status": "raw_audited_not_accepted", "created_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"), "videos": videos, "formal_events": 0, "formal_qa": 0, "hard_gates": ["never Fire360", "frame-level XML semantics must be verified", "source-group split, video segment policy, and QA eligibility not frozen"]}
    out = reports_root(data_root); out.mkdir(parents=True, exist_ok=True); path = out / "furg_raw_audit_v2.json"; path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8"); return path


def freeze_immersed_case_mapping(data_root: Path) -> Path:
    """Store documented raw-case codes privately; do not expose them in Event/QA."""
    source_root = data_root / "raw" / "immersed_tunnel" / "immersed_tunnel_mirror"
    readme = source_root / "README.md"
    files = sorted((source_root / "CFD-Data").glob("*.csv"))
    pattern = re.compile(r"^(70|100|130)(M|U)(\d{2})_devc\.csv$")
    mappings = []
    for path in files:
        match = pattern.match(path.name)
        if match is None:
            raise ValueError(f"unexpected immersed source filename: {path.name}")
        mappings.append({"opaque_ref": f"immersed-cfd-{len(mappings)+1:04d}", "raw_sha256": _sha256(path), "source_position_code": match.group(1), "lane_code": match.group(2), "exhaust_configuration_code": match.group(3)})
    payload = {"schema_version": "external-ood-private-mapping-0.1.0", "source_domain": "immersed_tunnel", "status": "not_a_public_label_file", "readme_sha256": _sha256(readme), "source_commit": subprocess.check_output(["git", "-C", str(source_root), "rev-parse", "HEAD"], text=True).strip(), "mapping_basis": "README describes six ignition-location codes and 32 smoke-exhaust configurations; task-label mapping remains unapproved", "records": mappings, "formal_events": 0, "formal_qa": 0}
    out = data_root / "external_ood" / "private" / "immersed_tunnel"; out.mkdir(parents=True, exist_ok=True); path = out / "case_mapping.json"; path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8"); return path


def audit_furg_annotation_coverage(data_root: Path) -> Path:
    """Count rectangle presence without inferring absent boxes are no-fire."""
    source_root = data_root / "raw" / "fire360" / "furg_fire_substitute"
    rows = []
    for xml_path in sorted(source_root.glob("*.xml")):
        blocks = re.findall(r"<frameNumber>(\d+)</frameNumber>\s*<annotations>(.*?)</annotations>", xml_path.read_text(errors="replace"), flags=re.S)
        ids = [int(frame_id) for frame_id, _ in blocks]
        positive = sum(bool(re.search(r"\d", content)) for _, content in blocks)
        rows.append({"xml_sha256": _sha256(xml_path), "frame_records": len(ids), "frames_with_rectangle_content": positive, "frames_without_rectangle_content": len(ids) - positive, "duplicate_frame_records": len(ids) - len(set(ids)), "first_frame": min(ids) if ids else None, "last_frame": max(ids) if ids else None})
    report = {"schema_version": "external-ood-annotation-coverage-0.1.0", "source_domain": "furg_fire_substitute", "status": "annotation_presence_audited_not_semantics_approved", "videos": rows, "interpretation": "no rectangle is not treated as no_fire", "formal_events": 0, "formal_qa": 0}
    out = reports_root(data_root); out.mkdir(parents=True, exist_ok=True); path = out / "furg_annotation_coverage.json"; path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8"); return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only external raw audit")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source", choices=("polyu", "polyu_rows", "furg", "furg_coverage", "immersed_mapping"), required=True)
    args = parser.parse_args()
    if args.source == "polyu":
        print(audit_polyu_workbooks(args.root))
    if args.source == "polyu_rows":
        print(audit_polyu_database_rows(args.root))
    if args.source == "furg":
        print(audit_furg_videos(args.root))
    if args.source == "furg_coverage":
        print(audit_furg_annotation_coverage(args.root))
    if args.source == "immersed_mapping":
        print(freeze_immersed_case_mapping(args.root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
