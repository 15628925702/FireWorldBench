"""Generate compact, source-separated model/baseline result tables."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def baseline_rows(report: dict[str, Any], track: str, coverage: str) -> list[dict[str, str]]:
    rows = []
    for name, value in report["methods"].items():
        score = value.get("score", {})
        task_scores = score.get("task_scores", {})
        metric = "track macro" if score.get("overall") is not None else next(iter(task_scores), "")
        number = score.get("overall")
        if number is None and len(task_scores) == 1:
            number = next(iter(task_scores.values()))
        rows.append({"track": track, "coverage": coverage, "method": name, "metric": metric, "score": "" if number is None else f"{number:.4f}", "status": value["status"]})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--s-baselines", type=Path, required=True)
    parser.add_argument("--i-baselines", type=Path, required=True)
    parser.add_argument("--s-model", type=Path, required=True)
    parser.add_argument("--i-model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = baseline_rows(read(args.s_baselines), "S", "nine tasks")
    rows.append({"track": "S", "coverage": "nine tasks", "method": "openai/gpt-4o-mini", "metric": "track macro", "score": f"{read(args.s_model)['overall']:.4f}", "status": "complete"})
    rows.extend(baseline_rows(read(args.i_baselines), "I", "L1-3 only"))
    i_model = read(args.i_model)
    rows.append({"track": "I", "coverage": "L1-3 only", "method": "openai/gpt-4o-mini", "metric": "L1-3", "score": f"{i_model['task_scores']['L1-3']:.4f}", "status": "complete"})
    rows.append({"track": "V", "coverage": "none", "method": "openai/gpt-4o-mini", "metric": "", "score": "", "status": "unsupported: fixed model has no video input"})
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "result_comparison.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("track", "coverage", "method", "metric", "score", "status"))
        writer.writeheader(); writer.writerows(rows)
    lines = ["# FDS Core Model and Baseline Comparison", "", "Scores are FDS track-level metrics, not FDS Overall. I has one released task; V is unsupported for the fixed model.", "", "| Track | Coverage | Method | Metric | Score | Status |", "| --- | --- | --- | --- | ---: | --- |"]
    lines.extend(f"| {r['track']} | {r['coverage']} | {r['method']} | {r['metric'] or 'n/a'} | {r['score'] or 'null'} | {r['status']} |" for r in rows)
    (args.output / "result_comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())