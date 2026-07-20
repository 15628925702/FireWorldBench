"""Build reproducible report, table, and evidence artifacts outside the frozen release."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from fireworld.coverage import coverage_matrix
from fireworld.release_verify import verify_fds_core


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_artifacts(release: Path, score: Path, predictions: Path, output: Path) -> dict[str, Any]:
    verification = verify_fds_core(release)
    if not verification["ok"]:
        raise ValueError("immutable FDS Core verification failed")
    report = _read(score)
    gold = _read(release / "private" / "qa_test_gold.json")
    predicted = {row["qa_id"]: row for row in _read(predictions)}
    rows = []
    for item in gold:
        prediction = predicted.get(item["qa_id"])
        if prediction is None:
            continue
        rows.append({
            "qa_id": item["qa_id"], "event_id": item["event_id"], "task_id": item["task_id"],
            "layer": item["layer"], "track": item["track"], "source_domain": item["source_domain"],
            "split": item["split"], "prediction_present": True,
            "gold_answer_sha256": hashlib.sha256(json.dumps(item["answer"], sort_keys=True).encode()).hexdigest(),
            "prediction_sha256": hashlib.sha256(json.dumps(prediction["answer"], sort_keys=True).encode()).hexdigest(),
        })
    output.mkdir(parents=True, exist_ok=True)
    _write(output / "release_verification.json", verification)
    _write(output / "score_report.json", report)
    _write(output / "evidence_matrix.json", rows)
    _write(output / "coverage_matrix.json", coverage_matrix())
    with (output / "task_scores.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("task_id", "score", "track", "partition"))
        writer.writeheader()
        for task_id, value in sorted(report["task_scores"].items()):
            writer.writerow({"task_id": task_id, "score": value, "track": report["track"], "partition": report["partition"]})
    lines = [
        "# FireWorldBench v2 Evaluation Report", "",
        f"- FDS Core verification: {'PASS' if verification['ok'] else 'FAIL'}",
        f"- Partition: {report['partition']}", f"- Track: {report['track']}",
        f"- Overall: {report['overall']}", f"- Missing predictions: {report['missing_predictions']}",
        "- Primary conclusions are FDS Core only. External sources remain independent candidate/substitute reporting inputs.",
        "- No LLM judge is used by this scorer. Calibration metrics are omitted because the prediction protocol has no confidence field.",
        "", "## Task scores", "", "| Task | Score |", "| --- | ---: |",
    ]
    lines.extend(f"| {task} | {value:.2f} |" for task, value in sorted(report["task_scores"].items()))
    (output / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"evidence_rows": len(rows), "verification": verification, "score": report}


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate final evaluation artifacts")
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--score", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_artifacts(args.release, args.score, args.predictions, args.output)
    print(json.dumps({"evidence_rows": result["evidence_rows"], "ok": result["verification"]["ok"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())