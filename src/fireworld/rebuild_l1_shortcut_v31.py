"""Create the v3.1 QA candidate with a time-balanced L1-1 task."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from fireworld.build_global_release import (
    labels,
    load_events,
    payload,
    qa,
    raw_for_event,
    sensor_fault,
    series,
)
from fireworld.mini_pilot import write_json
from fireworld.validation import validate_event_groups, validate_qa_semantics, validate_schema

VERSION = "fds-core-v3.1.0"
WINDOWS = (3, 6, 10, 20)
PER_CLASS_PER_WINDOW = 18


def l1_class(event: dict[str, Any]) -> str:
    value = str(labels(event).get("event_class", ""))
    return "no_fire" if value == "non_fire_disturbance" else value


def observation(ref: str, end: int) -> dict[str, Any]:
    return {
        "structured": {"ref": ref},
        "images": None,
        "video": None,
        "context": "Bounded early sensor window.",
        "time_window_s": [0.0, float(end)],
    }


def add_clean_question(
    root: Path,
    event: dict[str, Any],
    split: str,
    rows: list[dict[str, float]],
    klass: str,
    window: int,
    ordinal: int,
) -> dict[str, Any]:
    ref = payload(
        root,
        event["event_id"],
        "v3_1_l1_1",
        f"{klass}_w{window}_{ordinal:02d}",
        {
            "format": "bounded_sensor_window_v3_1",
            "start_s": 0,
            "end_s": window,
            "rows": series(rows, 0, window),
        },
    )
    item = qa(
        event,
        split,
        "L1-1",
        1000 + ordinal,
        observation(ref, window),
        {"class": klass},
        "Which attribution best explains this bounded early observation?",
    )
    item["provenance"]["builder_version"] = VERSION
    return item


def add_fault_question(
    root: Path,
    event: dict[str, Any],
    split: str,
    rows: list[dict[str, float]],
    window: int,
    ordinal: int,
) -> dict[str, Any]:
    fault_kind = ("drift", "stuck", "spike")[ordinal % 3]
    ref = payload(
        root,
        event["event_id"],
        "v3_1_l1_1",
        f"sensor_fault_w{window}_{ordinal:02d}",
        {
            "format": "bounded_sensor_window_v3_1",
            "start_s": 0,
            "end_s": window,
            "fault_injection": {
                "version": VERSION,
                "kind": fault_kind,
                "public_parameters": None,
            },
            "rows": sensor_fault(series(rows, 0, window), fault_kind),
        },
    )
    item = qa(
        event,
        split,
        "L1-1",
        2000 + ordinal,
        observation(ref, window),
        {"class": "sensor_fault"},
        "Which attribution best explains this bounded early observation?",
    )
    item["provenance"]["builder_version"] = VERSION
    return item


def build(root: Path) -> dict[str, Any]:
    event_pairs, batch_index = load_events(root)
    source = root / "qa" / "protocol_rebuild_v3" / "qa.json"
    questions: list[dict[str, Any]] = [
        item for item in json.loads(source.read_text()) if item["task_id"] != "L1-1"
    ]
    pools: dict[str, list[tuple[dict[str, Any], str, list[dict[str, float]]]]] = {
        "fire": [],
        "no_fire": [],
        "ventilation_disturbance": [],
    }
    for event, split in event_pairs:
        klass = l1_class(event)
        if klass in pools:
            pools[klass].append((event, split, raw_for_event(root, event, batch_index)))
    for value in pools.values():
        value.sort(key=lambda item: item[0]["event_id"])
    if any(len(value) < PER_CLASS_PER_WINDOW for value in pools.values()):
        raise ValueError({key: len(value) for key, value in pools.items()})
    l1_questions: list[dict[str, Any]] = []
    for klass, pool in pools.items():
        for window_index, window in enumerate(WINDOWS):
            for local_index in range(PER_CLASS_PER_WINDOW):
                index = (window_index * PER_CLASS_PER_WINDOW + local_index) % len(pool)
                event, split, rows = pool[index]
                l1_questions.append(
                    add_clean_question(
                        root,
                        event,
                        split,
                        rows,
                        klass,
                        window,
                        window_index * PER_CLASS_PER_WINDOW + local_index,
                    )
                )
    fire_pool = pools["fire"]
    for window_index, window in enumerate(WINDOWS):
        for local_index in range(PER_CLASS_PER_WINDOW):
            event, split, rows = fire_pool[window_index * PER_CLASS_PER_WINDOW + local_index]
            l1_questions.append(
                add_fault_question(
                    root,
                    event,
                    split,
                    rows,
                    window,
                    window_index * PER_CLASS_PER_WINDOW + local_index,
                )
            )
    questions.extend(l1_questions)
    errors = [
        error
        for item in questions
        for error in validate_schema(item, "qa.schema.json") + validate_qa_semantics(item)
    ]
    errors += validate_event_groups(questions)
    if errors:
        raise ValueError("v3.1 validation failed: " + "; ".join(errors[:10]))
    out = root / "qa" / "fds_core_v3_1"
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "qa.json", questions)
    counts = Counter(item["answer"]["fields"]["class"] for item in l1_questions)
    windows = {
        klass: dict(
            Counter(
                item["observation"]["time_window_s"][1]
                for item in l1_questions
                if item["answer"]["fields"]["class"] == klass
            )
        )
        for klass in counts
    }
    report = {
        "version": VERSION,
        "qa": len(questions),
        "l1_1_class_counts": dict(counts),
        "l1_1_window_counts": windows,
        "validation_errors": len(errors),
    }
    write_json(root / "reports" / "fds_core_v3_1_l1_1_rebuild.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.root.resolve()), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
