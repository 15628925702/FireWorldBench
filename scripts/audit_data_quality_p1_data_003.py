"""Read-only quality and grouping audit for P1-DATA-003."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3] / "3.数据集"
REPO = Path(__file__).resolve().parents[1]
MANIFEST = REPO / "项目治理" / "data_manifest_P1-DATA-001.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def csv_quality(path: Path) -> dict[str, object]:
    missing = 0
    non_numeric = 0
    rows = 0
    widths: Counter[int] = Counter()
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.reader(handle):
            rows += 1
            widths[len(row)] += 1
            for value in row:
                value = value.strip()
                if value == "" or value.lower() in {"nan", "na", "n/a", "null"}:
                    missing += 1
                else:
                    try:
                        number = float(value)
                        if not math.isfinite(number):
                            non_numeric += 1
                    except ValueError:
                        if rows > 2:
                            non_numeric += 1
    return {
        "rows": rows,
        "widths": dict(widths),
        "missing_cells": missing,
        "non_finite_or_non_numeric_cells": non_numeric,
    }


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
    files = manifest["source_files"]
    by_hash: defaultdict[str, list[str]] = defaultdict(list)
    zeros: list[str] = []
    for item in files:
        path = ROOT / Path(item["relative_path"])
        if path.stat().st_size == 0:
            zeros.append(item["relative_path"])
        by_hash[item["sha256"]].append(item["relative_path"])

    groups: dict[str, list[str]] = defaultdict(list)
    for item in files:
        if item["dataset_id"] != "D01":
            continue
        match = re.search(r"/(\d+)([MU])(\d{2})_devc\.csv$", item["relative_path"])
        if match:
            groups[match.group(1) + match.group(2)].append(match.group(3))

    csv_results = {}
    for item in files:
        if item["dataset_id"] in {"D01", "D03"} and item["relative_path"].lower().endswith(".csv"):
            path = ROOT / Path(item["relative_path"])
            csv_results[item["relative_path"]] = csv_quality(path)

    label_results = {}
    for item in files:
        if item["dataset_id"] in {"D05", "D06"} and item["relative_path"].lower().endswith(".txt"):
            path = ROOT / Path(item["relative_path"])
            label_results[item["relative_path"]] = {
                "bytes": path.stat().st_size,
                "empty": path.stat().st_size == 0,
                "line_count": len(path.read_text(encoding="utf-8", errors="replace").splitlines()),
            }

    print(json.dumps({
        "manifest_files": len(files),
        "zero_byte_files": zeros,
        "duplicate_hash_groups": [paths for paths in by_hash.values() if len(paths) > 1],
        "d01_case_groups": dict(groups),
        "csv_quality": csv_results,
        "visual_label_quality": label_results,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
