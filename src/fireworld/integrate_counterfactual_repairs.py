"""Integrate physically audited repair pairs into L3-3 without touching old raw."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from fireworld.build_global_release import load_events, nearest, observation, payload, qa
from fireworld.mini_pilot import write_json
from fireworld.validation import validate_event_groups, validate_qa_semantics, validate_schema

VERSION = "counterfactual-repair-integration-v3.0.0"


def load(path: Path) -> list[dict[str, float]]:
    with path.open(encoding="utf-8", newline="") as handle:
        raw = list(csv.reader(handle))
    names = raw[1]
    return [
        {name: float(value) for name, value in zip(names, values, strict=True)}
        for values in raw[2:]
        if len(values) == len(names)
    ]


def summary(rows: list[dict[str, float]], start: int, end: int) -> list[dict[str, float]]:
    return [nearest(rows, time) for time in range(start, end + 1)]


def max_temperature(row: dict[str, float]) -> float:
    return max(row[f"T_R{region}"] for region in range(1, 9))


def min_visibility(row: dict[str, float]) -> float:
    return min(row[f"V_R{region}"] for region in range(1, 9))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    event_pairs, _ = load_events(root)
    events = {event["event_id"]: (event, split) for event, split in event_pairs}
    qa_path = root / "qa" / "protocol_rebuild_v3" / "qa.json"
    questions: list[dict[str, Any]] = json.loads(qa_path.read_text())
    batch = root / "fds_runs" / "counterfactual_repair_v3"
    manifest = json.loads((batch / "input_manifest.json").read_text())["runs"]
    audit = json.loads(
        (
            root / "reports" / "production_batches" / "counterfactual_repair_v3_physical_audit.json"
        ).read_text()
    )
    passed = {item["run_key"] for item in audit["runs"] if item["pass"]}
    families: dict[str, list[dict[str, Any]]] = {}
    for item in manifest:
        families.setdefault(item["counterfactual_family"], []).append(item)
    accepted: list[str] = []
    for family, pair in sorted(families.items()):
        if len(pair) != 2:
            continue
        a, b = sorted(pair, key=lambda item: item["matrix_row"]["intervention"]["side"])
        a_run_ref = a["run_key"]
        if a["run_key"] not in passed:
            # The 300 HRR repair for P007-A was physically under-observable. Its
            # original 900 HRR run passed the frozen production physical audit,
            # so reuse that audited A side while retaining the stronger B repair.
            if family != "FWCF-P007" or b["run_key"] not in passed:
                continue
            original_audit = json.loads(
                (
                    root
                    / "reports"
                    / "production_batches"
                    / "production_batch_01_physical_audit.json"
                ).read_text()
            )
            if not any(
                item["event_id"] == a["event_id"] and item["pass"]
                for item in original_audit["runs"]
            ):
                continue
            a_rows = load(root / "fds_runs" / "production_batch_01" / "01_009" / "01_009_devc.csv")
            a_run_ref = "production_batch_01/01_009"
        else:
            a_rows = load(batch / a["run_key"] / f"{a['run_key']}_devc.csv")
        if b["run_key"] not in passed:
            continue
        b_rows = load(batch / b["run_key"] / f"{b['run_key']}_devc.csv")
        a80, b80 = nearest(a_rows, 80), nearest(b_rows, 80)
        delta_t = max_temperature(b80) - max_temperature(a80)
        delta_v = min_visibility(b80) - min_visibility(a80)
        if abs(delta_t) < 10.0 and abs(delta_v) < 3.0:
            continue
        event, split = events[a["event_id"]]
        ref = payload(
            root,
            event["event_id"],
            "l3_3_repair",
            family,
            {
                "format": "counterfactual_pair_v3",
                "family": family,
                "variable": "hrrpua",
                "metric": "maximum regional temperature at 80 seconds",
                "A_current_rows": summary(a_rows, 10, 20),
                "B_current_rows": summary(b_rows, 10, 20),
                "A_future_max_temperature_c": max_temperature(a80),
                "B_future_max_temperature_c": max_temperature(b80),
                "A_future_min_visibility_m": min_visibility(a80),
                "B_future_min_visibility_m": min_visibility(b80),
                "repair_provenance": {
                    "A_run": a_run_ref,
                    "B_run": b["run_key"],
                    "builder_version": VERSION,
                },
            },
        )
        answer = "A" if delta_t < 0 else "B"
        questions = [
            item
            for item in questions
            if not (item["task_id"] == "L3-3" and item["event_group"] == event["event_group"])
        ]
        questions.append(
            qa(
                event,
                split,
                "L3-3",
                100 + len(accepted),
                observation(ref, 10, 20, "Matched repaired A/B pair with only HRRPUA changed."),
                {"comparison": answer},
                "Which case has higher future maximum regional temperature at 80 seconds?",
            )
        )
        accepted.append(family)
    errors = [
        error
        for item in questions
        for error in validate_schema(item, "qa.schema.json") + validate_qa_semantics(item)
    ]
    errors += validate_event_groups(questions)
    if errors:
        raise ValueError("integration validation failed: " + "; ".join(errors[:10]))
    write_json(qa_path, questions)
    write_json(
        root / "reports" / "counterfactual_repair_v3_integration.json",
        {
            "status": "integrated_pending_global_audit",
            "accepted_families": accepted,
            "quarantined_families": sorted(set(families) - set(accepted)),
            "qa": len(questions),
        },
    )
    print(json.dumps({"accepted_families": accepted, "qa": len(questions)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
