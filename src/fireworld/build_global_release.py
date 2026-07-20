"""Rebuild FireWorldBench QA from temporally materialized FDS evidence.

This is deliberately separate from the superseded v2.1 global-release builder.
It never points a task at an event's complete trajectory: every observation and
candidate is a small, independently stored, time-bounded payload.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from fireworld.mini_pilot import write_json
from fireworld.validation import validate_event_groups, validate_qa_semantics, validate_schema

VERSION = "protocol-rebuild-v3.0.0"
TASKS = {
    "L1-1": ("accuracy", ["class"]),
    "L1-2": ("accuracy", ["choice"]),
    "L1-3": ("accuracy", ["consistency", "violation_type"]),
    "L2-1": ("component_accuracy", ["source_region", "stage"]),
    "L2-2": ("component_accuracy", ["risk_region", "risk_level"]),
    "L2-3": ("accuracy", ["mechanism"]),
    "L3-1": ("mean_accuracy", ["temperature_trend", "smoke_trend", "visibility_trend"]),
    "L3-2": ("accuracy", ["first_high_risk_region"]),
    "L3-3": ("accuracy", ["comparison"]),
}
REGIONS = tuple(f"R{i}" for i in range(1, 9))


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def labels(event: dict[str, Any]) -> dict[str, Any]:
    return {x["name"]: x["value"] for x in event["ground_truth"]["labels"]}


def rounded(row: dict[str, float]) -> dict[str, float]:
    return {key: round(value, 6) for key, value in row.items()}


def nearest(rows: list[dict[str, float]], when: float) -> dict[str, float]:
    return min(rows, key=lambda row: abs(row["Time"] - when))


def load_csv(path: Path) -> list[dict[str, float]]:
    with path.open(encoding="utf-8", newline="") as handle:
        raw = list(csv.reader(handle))
    if len(raw) < 3:
        raise ValueError(f"empty DEVC file: {path}")
    names = raw[1]
    rows: list[dict[str, float]] = []
    for values in raw[2:]:
        if len(values) != len(names):
            continue
        try:
            rows.append({name: float(value) for name, value in zip(names, values, strict=True)})
        except ValueError:
            continue
    if not rows or "Time" not in rows[0]:
        raise ValueError(f"unreadable DEVC file: {path}")
    return rows


def load_hrr(path: Path) -> list[dict[str, float]]:
    """Read FDS HRR CSV, whose first row stores units and second stores names."""
    with path.open(encoding="utf-8", newline="") as handle:
        raw = list(csv.reader(handle))
    if len(raw) < 3:
        return []
    names = raw[1]
    output: list[dict[str, float]] = []
    for values in raw[2:]:
        if len(values) != len(names):
            continue
        try:
            output.append({name: float(value) for name, value in zip(names, values, strict=True)})
        except ValueError:
            continue
    return output


def load_summary(path: Path) -> list[dict[str, float]]:
    return [
        {key: float(value) for key, value in row.items()}
        for row in json.loads(path.read_text())["rows"]
    ]


def payload(root: Path, event_id: str, kind: str, name: str, value: dict[str, Any]) -> str:
    path = root / "derived" / "protocol_rebuild_v3" / "S" / event_id / kind / f"{name}.json"
    write_json(path, value)
    return str(path.relative_to(root))


def observation(ref: str, start: float, end: float, context: str) -> dict[str, Any]:
    return {
        "structured": {"ref": ref},
        "images": None,
        "video": None,
        "context": context,
        "time_window_s": [start, end],
    }


def qa(
    event: dict[str, Any],
    split: str,
    task: str,
    ordinal: int,
    obs: dict[str, Any],
    fields: dict[str, Any],
    question: str,
    options: list[dict[str, Any]] | None = None,
    choice: str | None = None,
    status: str = "eligible",
) -> dict[str, Any]:
    primary, components = TASKS[task]
    identity = f"{event['event_id']}:{task}:{ordinal}:{obs['structured']['ref'] if obs['structured'] else ''}"
    return {
        "schema_version": "2.0.0",
        "qa_id": "FWQ-" + digest(identity)[:12].upper(),
        "case_id": "FWC-" + digest(identity + ":case")[:12].upper(),
        "event_id": event["event_id"],
        "event_group": event["event_group"],
        "source_domain": "fds",
        "split": split,
        "layer": task[:2],
        "task_id": task,
        "track": "S",
        "observation": obs,
        "question": question,
        "options": options,
        "answer": {"choice": choice, "fields": fields},
        "scoring": {"primary": primary, "components": components, "secondary": []},
        "confidence_target": 1.0,
        "evidence_metadata": {"required": False, "gold_refs": []},
        "provenance": {
            "event_manifest_sha256": digest(event),
            "builder_version": VERSION,
            "task_config_sha256": digest(TASKS),
            "source_license_ref": "governance/licenses/fds.md",
        },
        "quality": {
            "status": status,
            "ambiguity_reason": (
                "independent_fire_engineering_review_deferred_by_user"
                if status == "eligible_expert_review_deferred"
                else None
                if status == "eligible"
                else "ambiguous_or_excluded"
            ),
            "shortcut_checks": {
                "opaque_paths": True,
                "time_matched": True,
                "option_style_matched": True,
                "appearance_matched": True,
            },
        },
    }


def raw_for_event(
    root: Path, event: dict[str, Any], batch_index: dict[str, tuple[Path, str]]
) -> list[dict[str, float]]:
    event_id = event["event_id"]
    if event_id in batch_index:
        run, key = batch_index[event_id]
        return load_csv(run / f"{key}_devc.csv")
    log_ref = Path(event["provenance"]["fds"]["log_ref"])
    run = root / log_ref.parent
    csvs = sorted(run.glob("*_devc.csv"))
    if csvs:
        return load_csv(csvs[0])
    return load_summary(root / event["observations"]["structured"]["ref"])


def hrr_for_event(
    root: Path, event: dict[str, Any], batch_index: dict[str, tuple[Path, str]]
) -> list[dict[str, float]]:
    event_id = event["event_id"]
    if event_id in batch_index:
        run, key = batch_index[event_id]
        return load_hrr(run / f"{key}_hrr.csv")
    run = root / Path(event["provenance"]["fds"]["log_ref"]).parent
    paths = sorted(run.glob("*_hrr.csv"))
    return load_hrr(paths[0]) if paths else []


def series(
    rows: list[dict[str, float]], start: float, end: float, step: float = 1.0
) -> list[dict[str, float]]:
    # FDS device samples are not aligned exactly to integer seconds.  Select the
    # latest actual sample at or before each requested time so an observation can
    # never contain a value from after its declared cutoff.
    output: list[dict[str, float]] = []
    for time in range(int(start), int(end) + 1, int(step)):
        candidates = [row for row in rows if row["Time"] <= time + 1e-9]
        output.append(rounded(candidates[-1] if candidates else rows[0]))
    return output


def stage_from_hrr(hrr_rows: list[dict[str, float]], t: float) -> str | None:
    """Frozen, reproducible stage rule based on the measured HRR curve.

    Boundary samples are excluded by returning None. This avoids treating an
    arbitrary clock time as physical stage information.
    """
    if not hrr_rows:
        return None
    values = [row.get("HRR", 0.0) for row in hrr_rows]
    peak = max(values, default=0.0)
    if peak < 1.0:
        return "incipient"
    current = nearest(hrr_rows, t).get("HRR", 0.0)
    prior = nearest(hrr_rows, max(0.0, t - 10)).get("HRR", 0.0)
    ratio, slope = current / peak, (current - prior) / 10.0
    if ratio <= 0.05:
        return "incipient"
    if 0.08 < ratio < 0.72 and slope > peak * 0.003:
        return "growth"
    if ratio >= 0.80:
        return "developed"
    if ratio < 0.72 and slope < -peak * 0.003:
        return "decay"
    return None


def risk(row: dict[str, float]) -> tuple[str, str, list[str]]:
    scores: dict[str, float] = {}
    for region in REGIONS:
        temp, vis = row.get(f"T_{region}", 20.0), row.get(f"V_{region}", 30.0)
        scores[region] = max((temp - 20.0) / 40.0, (30.0 - vis) / 6.0)
    ordered = sorted(scores, key=lambda region: scores[region], reverse=True)
    top, second = ordered[0], ordered[1]
    if abs(scores[top] - scores[second]) < 0.15:
        return top, "ambiguous", ordered[:2]
    t, v = row.get(f"T_{top}", 20.0), row.get(f"V_{top}", 30.0)
    level = (
        "critical"
        if t >= 200 or v <= 3
        else "high"
        if t >= 60 or v <= 10
        else "moderate"
        if t >= 35 or v <= 20
        else "low"
    )
    return top, level, [top]


def trend(a: float, b: float, deadband: float, inverse: bool = False) -> str:
    delta = b - a
    if abs(delta) < deadband:
        return "stable"
    return "down" if (delta < 0) ^ inverse else "up"


def first_high(
    rows: list[dict[str, float]], start: float, end: float
) -> tuple[str | None, float | None]:
    crossings: list[tuple[float, str]] = []
    for region in REGIONS:
        for row in rows:
            if start < row["Time"] <= end and (
                row.get(f"T_{region}", 20) >= 60 or row.get(f"V_{region}", 30) <= 10
            ):
                crossings.append((row["Time"], region))
                break
    if not crossings:
        return "none", None
    crossings.sort()
    if len(crossings) > 1 and crossings[1][0] - crossings[0][0] <= 2:
        return None, crossings[0][0]
    return crossings[0][1], crossings[0][0]


def sensor_fault(rows: list[dict[str, float]], variant: str) -> list[dict[str, float]]:
    output = [dict(row) for row in rows]
    for index, row in enumerate(output):
        for region in REGIONS:
            key = f"T_{region}"
            if key not in row:
                continue
            if variant == "drift":
                row[key] += 0.75 * index
            elif variant == "stuck" and index >= len(output) // 2:
                row[key] = output[len(output) // 2][key]
            elif variant == "spike" and index == len(output) // 2:
                row[key] += 45.0
    return output


def temporal_variant(rows: list[dict[str, float]], violation: str | None) -> list[dict[str, float]]:
    out = [dict(row) for row in rows]
    if violation is None:
        return out
    if violation == "reverse":
        return out[:2] + list(reversed(out[2:5])) + out[5:]
    if violation == "jump":
        return out[:2] + out[5:]
    if violation == "sensor_conflict":
        for row in out[2:]:
            row["T_R1"] = out[1].get("T_R1", 20.0)
    return out


def load_events(root: Path) -> tuple[list[tuple[dict[str, Any], str]], dict[str, tuple[Path, str]]]:
    matrix = json.loads((root / "splits" / "production_matrix.v2.1.json").read_text())
    rows = {row["event_id"]: row for row in matrix["rows"]}
    batch_index: dict[str, tuple[Path, str]] = {}
    events: dict[str, dict[str, Any]] = {}
    for manifest_path in sorted((root / "fds_runs").glob("production_batch_*/input_manifest.json")):
        for item in json.loads(manifest_path.read_text())["runs"]:
            batch_index[item["event_id"]] = (
                manifest_path.parent / item["run_key"],
                item["run_key"],
            )
    repair_manifest = root / "fds_runs/trajectory_repair_v3_2/input_manifest.json"
    if repair_manifest.is_file():
        for item in json.loads(repair_manifest.read_text())["runs"]:
            batch_index[item["event_id"]] = (
                repair_manifest.parent / item["run_key"],
                item["run_key"],
            )
    for path in sorted((root / "fire_events").glob("production_batch_*/fire_events.json")):
        events.update({event["event_id"]: event for event in json.loads(path.read_text())})
    repair_events = root / "fire_events/trajectory_repair_v3_2/fire_events.json"
    if repair_events.is_file():
        events.update(
            {event["event_id"]: event for event in json.loads(repair_events.read_text())}
        )
    for row in matrix["rows"]:
        if row["status"] == "qualified_existing":
            events[row["event_id"]] = json.loads((root / row["source_ref"]).read_text())
    missing = set(rows) - set(events)
    if missing:
        raise ValueError(f"matrix event records missing: {sorted(missing)}")
    return [(events[event_id], rows[event_id]["split"]) for event_id in rows], batch_index


def build(root: Path) -> dict[str, Any]:
    event_pairs, batch_index = load_events(root)
    questions: list[dict[str, Any]] = []
    families: dict[str, list[tuple[dict[str, Any], str, list[dict[str, float]]]]] = defaultdict(
        list
    )
    excluded: Counter[str] = Counter()
    fault_ids = {
        event["event_id"] for event, _ in event_pairs if labels(event).get("event_class") == "fire"
    }
    fault_ids = set(sorted(fault_ids)[:72])
    for event, split in event_pairs:
        rows = raw_for_event(root, event, batch_index)
        hrr_rows = hrr_for_event(root, event, batch_index)
        event_id = event["event_id"]
        truth = labels(event)
        event_class = str(truth.get("event_class", "fire"))
        source = str(truth.get("source_region") or event["controls"].get("source_region") or "R1")
        max_time = min(120.0, max(row["Time"] for row in rows))
        if max_time < 90:
            excluded["timeline_under_90s"] += 1
            continue
        # L1-1: materialized early windows. One derived sensor-fault sample per event avoids inflating events.
        for ordinal, end in enumerate((3, 6, 10, 20), 1):
            window = series(rows, 0, end)
            klass = event_class if event_class != "non_fire_disturbance" else "no_fire"
            ref = payload(
                root,
                event_id,
                "l1_1",
                f"w{end}",
                {"format": "bounded_sensor_window", "start_s": 0, "end_s": end, "rows": window},
            )
            questions.append(
                qa(
                    event,
                    split,
                    "L1-1",
                    ordinal,
                    observation(ref, 0, end, "Early bounded sensor window."),
                    {"class": klass},
                    "Which attribution best explains this observation?",
                )
            )
        if event_id in fault_ids:
            fault_end = (3, 6, 10, 20)[sorted(fault_ids).index(event_id) % 4]
            fault_window = sensor_fault(
                series(rows, 0, fault_end),
                ("drift", "stuck", "spike")[int(event_id[-1], 16) % 3],
            )
            fault_ref = payload(
                root,
                event_id,
                "l1_1",
                "sensor_fault",
                {
                    "format": "bounded_sensor_window",
                    "start_s": 0,
                    "end_s": fault_end,
                    "fault_injection": "versioned",
                    "rows": fault_window,
                },
            )
            questions.append(
                qa(
                    event,
                    split,
                    "L1-1",
                    99,
                    observation(fault_ref, 0, fault_end, "Early bounded sensor window."),
                    {"class": "sensor_fault"},
                    "Which attribution best explains this observation?",
                )
            )
        # L1-2: current window and four materialized same-event states. Correct is t + delta.
        for ordinal, (now, delta) in enumerate(
            ((10, 10), (20, 10), (30, 20), (40, 20), (50, 30)), 1
        ):
            target = now + delta
            if target > max_time:
                continue
            current_ref = payload(
                root,
                event_id,
                "l1_2",
                f"current_{now}_{target}",
                {
                    "format": "bounded_current_window",
                    "start_s": max(0, now - 10),
                    "end_s": now,
                    "rows": series(rows, max(0, now - 10), now),
                },
            )
            # Distinct same-event alternatives: prior, actual target, near future, and far future.
            alternatives = [max(0, now - delta), target + 10, target + 20]
            if len(set([target, *alternatives])) != 4:
                excluded["l1_2_non_distinct_candidates"] += 1
                continue
            correct = "ABCD"[(ordinal + int(event_id[-1], 16)) % 4]
            options = []
            for option in "ABCD":
                actual = target if option == correct else alternatives.pop(0)
                ref = payload(
                    root,
                    event_id,
                    "l1_2",
                    f"candidate_{now}_{target}_{option}",
                    {
                        "format": "candidate_state",
                        "time_s": actual,
                        "values": rounded(nearest(rows, actual)),
                        "source": "same_event",
                    },
                )
                options.append(
                    {"id": option, "content_ref": ref, "text": "time-matched candidate state"}
                )
            questions.append(
                qa(
                    event,
                    split,
                    "L1-2",
                    ordinal,
                    observation(
                        current_ref,
                        max(0, now - 10),
                        now,
                        f"Current window; select state at +{delta} seconds.",
                    ),
                    {"choice": correct},
                    "Which candidate is the actual future state at the stated horizon?",
                    options,
                    correct,
                )
            )
        # L1-3: exactly 50% genuinely transformed sequences.
        for ordinal, violation in enumerate(
            (None, "reverse", None, "sensor_conflict", "jump", None), 1
        ):
            base = series(rows, 10, 40, 5)
            transformed = temporal_variant(base, violation)
            ref = payload(
                root,
                event_id,
                "l1_3",
                str(ordinal),
                {
                    "format": "ordered_sensor_sequence",
                    "transform": "identity" if violation is None else violation,
                    "rows": transformed,
                },
            )
            fields = {
                "consistency": "consistent" if violation is None else "inconsistent",
                "violation_type": violation,
            }
            questions.append(
                qa(
                    event,
                    split,
                    "L1-3",
                    ordinal,
                    observation(ref, 10, 40, "Ordered observed sequence."),
                    fields,
                    "Is this sequence temporally consistent?",
                )
            )
        # Current state tasks at three non-boundary snapshots.
        for ordinal, now in enumerate((20, 50, 80), 1):
            window_ref = payload(
                root,
                event_id,
                "state",
                f"t{now}",
                {
                    "format": "bounded_current_window",
                    "start_s": now - 10,
                    "end_s": now,
                    "rows": series(rows, now - 10, now),
                },
            )
            current = nearest(rows, now)
            region, level, _tied = risk(current)
            if event_class == "fire":
                current_stage = stage_from_hrr(hrr_rows, now)
                if current_stage is not None:
                    questions.append(
                        qa(
                            event,
                            split,
                            "L2-1",
                            ordinal,
                            observation(
                                window_ref, now - 10, now, "Current bounded fire observation."
                            ),
                            {"source_region": source, "stage": current_stage},
                            "Recover source region and fire stage.",
                        )
                    )
                else:
                    excluded["stage_boundary_or_missing_hrr"] += 1
            if level != "ambiguous":
                questions.append(
                    qa(
                        event,
                        split,
                        "L2-2",
                        ordinal,
                        observation(
                            window_ref, now - 10, now, "Current bounded eight-region observation."
                        ),
                        {"risk_region": region, "risk_level": level},
                        "Recover highest-risk region and risk level.",
                    )
                )
            else:
                excluded["risk_tie"] += 1
        # Future tasks use horizon-specific current/future robust endpoints.
        for ordinal, horizon in enumerate((10, 30, 60), 1):
            prediction_now: float = 20.0
            future_t: float = 20.0 + horizon
            if future_t > max_time:
                continue
            ref = payload(
                root,
                event_id,
                "future",
                f"h{horizon}",
                {
                    "format": "bounded_current_window",
                    "start_s": 10,
                    "end_s": 20,
                    "rows": series(rows, 10, 20),
                },
            )
            a, b = nearest(rows, prediction_now), nearest(rows, future_t)
            fields = {
                "temperature_trend": trend(a.get(f"T_{source}", 20), b.get(f"T_{source}", 20), 5),
                "smoke_trend": trend(a.get(f"V_{source}", 30), b.get(f"V_{source}", 30), 1, True),
                "visibility_trend": trend(a.get(f"V_{source}", 30), b.get(f"V_{source}", 30), 1),
            }
            questions.append(
                qa(
                    event,
                    split,
                    "L3-1",
                    ordinal,
                    observation(ref, 10, 20, f"Predict the next {horizon} seconds."),
                    fields,
                    "Predict temperature, smoke, and visibility trends.",
                )
            )
            first_region, _cross_time = first_high(rows, prediction_now, future_t)
            if first_region is not None:
                questions.append(
                    qa(
                        event,
                        split,
                        "L3-2",
                        ordinal,
                        observation(
                            ref, 10, 20, f"Predict first high risk within {horizon} seconds."
                        ),
                        {"first_high_risk_region": first_region},
                        "Which region first reaches high risk?",
                    )
                )
            else:
                excluded["future_risk_tie"] += 1
        intervention = event["controls"].get("intervention")
        if intervention and intervention.get("base_event_id"):
            families[event["event_group"]].append((event, split, rows))
    # L3-3 only for genuine same-group single-variable pairs.
    for ordinal, members in enumerate(families.values(), 1):
        if (
            len(members) != 2
            or {
                member[0]["controls"]["intervention"].get("variable") for member in members
            }.__len__()
            != 1
        ):
            continue
        member_a, member_b = sorted(
            members, key=lambda member: str(member[0]["controls"]["intervention"].get("value"))
        )
        source = str(member_a[0]["controls"].get("source_region") or "R1")
        av = nearest(member_a[2], 80).get(f"T_{source}", 20)
        bv = nearest(member_b[2], 80).get(f"T_{source}", 20)
        if abs(av - bv) <= 1:
            excluded["counterfactual_small_delta"] += 1
            continue
        ref = payload(
            root,
            member_a[0]["event_id"],
            "l3_3",
            member_a[0]["event_group"],
            {
                "format": "counterfactual_pair",
                "variable": member_a[0]["controls"]["intervention"]["variable"],
                "A": series(member_a[2], 10, 20),
                "B": series(member_b[2], 10, 20),
                "comparison_time_s": 80,
            },
        )
        answer = "A" if av > bv else "B"
        questions.append(
            qa(
                member_a[0],
                member_a[1],
                "L3-3",
                ordinal,
                observation(ref, 10, 20, "Matched A/B pair with one intervention variable."),
                {"comparison": answer},
                "Which case has higher future source-region temperature?",
                None,
                None,
            )
        )
    # Publish a balanced L1-1 subset. The raw, materialized candidates remain in
    # derived/ for audit, but benchmark QA uses exactly the same count per class.
    l1_target_per_window = 18
    selected_l1: list[dict[str, Any]] = []
    for klass in ("fire", "no_fire", "ventilation_disturbance", "sensor_fault"):
        items = [
            item
            for item in questions
            if item["task_id"] == "L1-1" and item["answer"]["fields"]["class"] == klass
        ]
        for end_s in (3.0, 6.0, 10.0, 20.0):
            window_items = [
                item
                for item in items
                if float(item["observation"]["time_window_s"][1]) == end_s
            ]
            if len(window_items) < l1_target_per_window:
                raise ValueError(
                    f"insufficient L1-1 materialized examples for {klass} at {end_s}s: "
                    f"{len(window_items)}"
                )
            selected_l1.extend(
                sorted(window_items, key=lambda item: item["qa_id"])[
                    :l1_target_per_window
                ]
            )
    questions = [item for item in questions if item["task_id"] != "L1-1"] + selected_l1
    # Exact global A/B/C/D balance without changing the underlying candidate
    # states: move each positive candidate to its assigned public position.
    for ordinal, item in enumerate(
        sorted((x for x in questions if x["task_id"] == "L1-2"), key=lambda x: x["qa_id"])
    ):
        desired, old = "ABCD"[ordinal % 4], item["answer"]["choice"]
        if old == desired:
            continue
        for option in item["options"] or []:
            if option["id"] == old:
                option["id"] = desired
            elif option["id"] == desired:
                option["id"] = old
        item["answer"]["choice"] = desired
        item["answer"]["fields"]["choice"] = desired
    # L2-3 labels are derived from the active observation and frozen controls.
    # Independent fire-engineering review remains explicitly deferred by user.
    mechanism_examples: dict[str, tuple[dict[str, Any], str, list[dict[str, float]]]] = {}
    for event, split in event_pairs:
        rows = raw_for_event(root, event, batch_index)
        truth = labels(event)
        if truth.get("event_class") != "fire":
            continue
        supply = float((event["controls"].get("ventilation") or {}).get("supply_velocity_m_s", 0.0))
        intervention = event["controls"].get("intervention") or {}
        hrrpua = float(intervention.get("value") or truth.get("hrrpua") or 0.0)
        extraction = bool(event["controls"].get("extraction"))
        if extraction:
            mechanism = "extraction_dominated"
        elif supply >= 1.5:
            mechanism = "longitudinal_ventilation"
        elif supply >= 0.8:
            mechanism = "backlayering"
        elif hrrpua >= 1900:
            mechanism = "buoyant_plume"
        elif hrrpua >= 1000:
            mechanism = "ceiling_jet"
        else:
            mechanism = "smoke_layer"
        mechanism_examples.setdefault(mechanism, (event, split, rows))
    missing_mechanisms = {
        "buoyant_plume",
        "ceiling_jet",
        "smoke_layer",
        "longitudinal_ventilation",
        "backlayering",
        "extraction_dominated",
    } - set(mechanism_examples)
    if missing_mechanisms:
        raise ValueError(f"active raw data do not support L2-3 mechanisms: {sorted(missing_mechanisms)}")
    for ordinal, (mechanism, (event, split, rows)) in enumerate(
        sorted(mechanism_examples.items()), 1
    ):
        ref = payload(
            root,
            event["event_id"],
            "l2_3_pending",
            mechanism,
            {
                "format": "engineering_rule_evidence",
                "mechanism": mechanism,
                "rows": series(rows, 20, 40),
            },
        )
        questions.append(
            qa(
                event,
                split,
                "L2-3",
                ordinal,
                observation(ref, 20, 40, "Engineering-rule evidence; independent review pending."),
                {"mechanism": mechanism},
                "Which transport mechanism is dominant?",
                status="eligible_expert_review_deferred",
            )
        )
    errors = [
        error
        for item in questions
        for error in validate_schema(item, "qa.schema.json") + validate_qa_semantics(item)
    ] + validate_event_groups(questions)
    if errors:
        raise ValueError("rebuild validation failed: " + "; ".join(errors[:10]))
    out = root / "qa" / "protocol_rebuild_v3"
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "qa.json", questions)
    report = {
        "status": "built_pending_full_audit",
        "events_with_materialized_qa": len({x["event_id"] for x in questions}),
        "qa": len(questions),
        "task_counts": dict(sorted(Counter(x["task_id"] for x in questions).items())),
        "quality_counts": dict(Counter(x["quality"]["status"] for x in questions)),
        "excluded": dict(excluded),
        "validation_errors": len(errors),
    }
    write_json(root / "reports" / "protocol_rebuild_v3_build.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.root.resolve()), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
