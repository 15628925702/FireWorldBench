"""Read-only external raw audits; emits reports only, never Events or QA."""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

def digest(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def polyu(root: Path) -> dict[str, object]:
    base = root / "raw/polyu/repo/2020_TUST_paper"
    ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    rows = []
    for p in sorted(base.glob("*.xlsx")):
        with ZipFile(p) as z:
            workbook = ET.fromstring(z.read("xl/workbook.xml"))
            sheets = [x.attrib["name"] for x in workbook.findall("x:sheets/x:sheet", ns)]
            shared = []
            if "xl/sharedStrings.xml" in z.namelist():
                shared_xml = ET.fromstring(z.read("xl/sharedStrings.xml"))
                shared = ["".join(x.itertext()) for x in shared_xml.findall("x:si", ns)]
            first_sheet = next(name for name in z.namelist() if name.startswith("xl/worksheets/sheet"))
            cells = ET.fromstring(z.read(first_sheet)).findall(".//x:row", ns)[:3]
            sample_rows = []
            for row in cells:
                values = []
                for cell in row.findall("x:c", ns):
                    value = cell.findtext("x:v", default="", namespaces=ns)
                    values.append(shared[int(value)] if cell.attrib.get("t") == "s" and value else value)
                sample_rows.append(values)
        rows.append({"file": p.name, "sha256": digest(p), "bytes": p.stat().st_size, "sheets": sheets, "first_sheet_sample_rows": sample_rows})
    return {"source": "polyu", "status": "raw_audited_not_accepted", "workbooks": rows,
            "formal_events": 0, "formal_qa": 0,
            "hard_gates": ["workbook field and unit semantics not yet extracted", "license evidence not verified", "no task rules or split audit"]}

def furg(root: Path) -> dict[str, object]:
    base = root / "raw/fire360/furg_fire_substitute"
    xml_by_stem = {p.stem.casefold(): p for p in base.glob("*.xml")}
    rows = []
    for v in sorted(base.glob("*.mp4")):
        x = xml_by_stem.get(v.stem.casefold())
        probe = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,codec_name,avg_frame_rate,width,height", "-of", "json", str(v)]))
        stream = next(s for s in probe["streams"] if s["codec_type"] == "video")
        frames = [] if x is None else [int(n) for n in re.findall(r"<frameNumber>(\d+)</frameNumber>", x.read_text(errors="replace"))]
        duration = float(probe["format"]["duration"])
        raw = subprocess.check_output(["ffmpeg", "-v", "error", "-ss", str(duration * .1), "-i", str(v), "-vf", "fps=1/2,scale=32:32,format=gray", "-frames:v", "5", "-f", "rawvideo", "-"])
        means = [sum(raw[i:i + 1024]) / 1024 for i in range(0, len(raw), 1024) if len(raw[i:i + 1024]) == 1024]
        rows.append({"video_sha256": digest(v), "bytes": v.stat().st_size, "xml_present": x is not None, "xml_sha256": digest(x) if x else None, "duration_s": duration, "codec": stream.get("codec_name"), "fps": stream.get("avg_frame_rate"), "width": stream.get("width"), "height": stream.get("height"), "annotated_frames": len(frames), "annotation_span": [frames[0], frames[-1]] if frames else None, "sample_gray_means": means, "sample_dynamic": max([abs(a-b) for a,b in zip(means, means[1:])], default=0) > .5, "sample_black": bool(means) and max(means) < 2})
    return {"source": "furg_fire_substitute", "status": "raw_audited_not_accepted", "videos": rows,
            "formal_events": 0, "formal_qa": 0,
            "hard_gates": ["must remain substitute, not Fire360", "dynamic/black-frame audit not complete", "XML-video frame alignment not complete", "group split and QA eligibility not complete"]}

def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--root", type=Path, required=True); ap.add_argument("--out", type=Path, required=True); args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    for name, report in [("polyu_raw_audit.json", polyu(args.root)), ("furg_raw_audit.json", furg(args.root))]:
        (args.out / name).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0
if __name__ == "__main__": raise SystemExit(main())
