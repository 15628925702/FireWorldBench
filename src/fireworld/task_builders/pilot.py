"""Fail-closed builders for the three pilot representative tasks."""

from __future__ import annotations

import hashlib
from typing import Any

from fireworld.contracts import TASKS


def _hash(value: Any) -> str:
    return hashlib.sha256(repr(value).encode()).hexdigest()


def _base(event: dict[str, Any], task_id: str, track: str, split: str) -> dict[str, Any]:
    if event.get("source_domain") != "fds" or event.get("status") not in {"candidate", "eligible"}:
        raise ValueError("pilot builders require a candidate/eligible FDS Fire Event")
    if event.get("provenance", {}).get("fds") is None:
        raise ValueError("pilot builders require FDS provenance")
    eid = str(event["event_id"])
    gid = str(event["event_group"])
    return {
        "schema_version": "2.0.0",
        "qa_id": "FWQ-" + _hash((eid, task_id, track))[:12].upper(),
        "case_id": "FWC-" + _hash((eid, task_id, split))[:12].upper(),
        "event_id": eid,
        "event_group": gid,
        "source_domain": "fds",
        "split": split,
        "layer": task_id[:2],
        "task_id": task_id,
        "track": track,
        "confidence_target": 1.0,
        "evidence_metadata": {"required": False, "gold_refs": []},
        "provenance": {
            "event_manifest_sha256": _hash(event),
            "builder_version": "pilot-builders-0.1.0",
            "task_config_sha256": _hash(TASKS),
            "source_license_ref": "governance/licenses/fds.md",
        },
        "quality": {
            "status": "eligible",
            "ambiguity_reason": None,
            "shortcut_checks": {
                "opaque_paths": True,
                "time_matched": True,
                "option_style_matched": None,
                "appearance_matched": None,
            },
        },
    }


def _labels(event: dict[str, Any]) -> dict[str, Any]:
    return {item["name"]: item["value"] for item in event["ground_truth"]["labels"]}


def _observation(
    event: dict[str, Any], track: str, context: str, window: list[float]
) -> dict[str, Any]:
    observations = event["observations"]
    if track == "S":
        structured = observations.get("structured")
        if structured is None:
            raise ValueError("S track requires structured observation")
        return {
            "structured": {"ref": structured["ref"]},
            "images": None,
            "video": None,
            "context": context,
            "time_window_s": window,
        }
    if track == "I":
        images = observations.get("images")
        if not images:
            raise ValueError("I track requires ordered image observations")
        return {
            "structured": None,
            "images": [item["ref"] for item in images],
            "video": None,
            "context": context,
            "time_window_s": window,
        }
    if track == "V":
        video = observations.get("video")
        if video is None:
            raise ValueError("V track requires a video observation")
        return {
            "structured": None,
            "images": None,
            "video": video["ref"],
            "context": context,
            "time_window_s": window,
        }
    raise ValueError(f"unsupported track: {track}")


def build_l1_2(event: dict[str, Any], track: str = "S", split: str = "train") -> dict[str, Any]:
    row = _base(event, "L1-2", track, split)
    labels = _labels(event)
    choice = labels.get("choice")
    if choice not in {"A", "B", "C", "D"}:
        raise ValueError("L1-2 needs a deterministic A/B/C/D choice label")
    row.update(
        {
            "observation": _observation(
                event,
                track,
                "Next-state candidate set; labels withheld from observation.",
                [0, 10],
            ),
            "question": "Which candidate is the next state?",
            "options": [
                {"id": x, "content_ref": None, "text": f"candidate {x}"}
                for x in ("A", "B", "C", "D")
            ],
            "answer": {"choice": choice, "fields": {"choice": choice}},
            "scoring": {"primary": "accuracy", "components": ["choice"], "secondary": []},
        }
    )
    return row


def build_l2_1(event: dict[str, Any], track: str = "S", split: str = "train") -> dict[str, Any]:
    row = _base(event, "L2-1", track, split)
    labels = _labels(event)
    if not {"source_region", "stage"}.issubset(labels):
        raise ValueError("L2-1 needs source_region and stage labels from provenance")
    row.update(
        {
            "observation": _observation(event, track, "Eight-region layout.", [20, 40]),
            "question": "Recover source region and stage.",
            "options": None,
            "answer": {
                "choice": None,
                "fields": {"source_region": labels["source_region"], "stage": labels["stage"]},
            },
            "scoring": {
                "primary": "component_accuracy",
                "components": ["source_region", "stage"],
                "secondary": ["joint_exact_match"],
            },
        }
    )
    return row


def build_l3_3(event: dict[str, Any], track: str = "S", split: str = "train") -> dict[str, Any]:
    row = _base(event, "L3-3", track, split)
    labels = _labels(event)
    if "comparison" not in labels:
        raise ValueError("L3-3 needs a deterministic comparison label")
    if event.get("controls", {}).get("intervention") is None:
        raise ValueError("L3-3 needs a declared one-variable counterfactual intervention")
    row.update(
        {
            "observation": _observation(
                event,
                track,
                "A/B differ by one declared intervention.",
                [20, 40],
            ),
            "question": "Which counterfactual has the stronger outcome?",
            "options": [
                {"id": x, "content_ref": None, "text": f"candidate {x}"} for x in ("A", "B", "C")
            ],
            "answer": {"choice": None, "fields": {"comparison": labels["comparison"]}},
            "scoring": {
                "primary": "accuracy",
                "components": ["comparison"],
                "secondary": ["counterfactual_consistency"],
            },
        }
    )
    return row


def build_l1_1(event: dict[str, Any], track: str = "S", split: str = "train") -> dict[str, Any]:
    row = _base(event, "L1-1", track, split)
    value = _labels(event).get("class")
    if value not in {"fire", "no_fire", "ventilation_disturbance", "sensor_fault"}:
        raise ValueError("L1-1 needs a fixed four-class attribution label")
    row.update(
        {
            "observation": _observation(
                event, track, "Early multi-sensor or visual observation.", [3, 20]
            ),
            "question": "Which attribution best explains the early observation?",
            "options": None,
            "answer": {"choice": None, "fields": {"class": value}},
            "scoring": {
                "primary": "accuracy",
                "components": ["class"],
                "secondary": ["macro_f1", "ece", "brier_score"],
            },
        }
    )
    return row


def build_l1_3(event: dict[str, Any], track: str = "S", split: str = "train") -> dict[str, Any]:
    row = _base(event, "L1-3", track, split)
    labels = _labels(event)
    consistency = labels.get("consistency")
    violation = labels.get("violation_type")
    valid = {"reverse", "jump", "disappearance", "direction_flip", "sensor_conflict"}
    if consistency not in {"consistent", "inconsistent"}:
        raise ValueError("L1-3 needs a consistency label")
    if consistency == "inconsistent" and violation not in valid:
        raise ValueError("inconsistent L1-3 requires a valid violation_type")
    if consistency == "consistent" and violation is not None:
        raise ValueError("consistent L1-3 requires violation_type=null")
    row.update(
        {
            "observation": _observation(event, track, "Ordered temporal sequence.", [10, 40]),
            "question": "Is this sequence temporally consistent?",
            "options": None,
            "answer": {
                "choice": None,
                "fields": {"consistency": consistency, "violation_type": violation},
            },
            "scoring": {
                "primary": "accuracy",
                "components": ["consistency"],
                "secondary": ["violation_type_accuracy"],
            },
        }
    )
    return row


def build_l2_2(event: dict[str, Any], track: str = "S", split: str = "train") -> dict[str, Any]:
    row = _base(event, "L2-2", track, split)
    labels = _labels(event)
    region = labels.get("risk_region")
    level = labels.get("risk_level")
    if region not in {f"R{index}" for index in range(1, 9)} or level not in {
        "low",
        "moderate",
        "high",
        "critical",
    }:
        raise ValueError("L2-2 needs deterministic risk_region and risk_level labels")
    row.update(
        {
            "observation": _observation(
                event, track, "Eight-region current risk observation.", [20, 40]
            ),
            "question": "Recover the current highest-risk region and risk level.",
            "options": None,
            "answer": {"choice": None, "fields": {"risk_region": region, "risk_level": level}},
            "scoring": {
                "primary": "component_accuracy",
                "components": ["risk_region", "risk_level"],
                "secondary": ["joint_exact_match"],
            },
        }
    )
    return row


def build_l2_3(event: dict[str, Any], track: str = "S", split: str = "train") -> dict[str, Any]:
    row = _base(event, "L2-3", track, split)
    mechanism = _labels(event).get("mechanism")
    valid = {
        "buoyant_plume",
        "ceiling_jet",
        "smoke_layer",
        "longitudinal_ventilation",
        "backlayering",
        "extraction_dominated",
    }
    if mechanism not in valid:
        raise ValueError("L2-3 needs one of the six fixed mechanism labels")
    row.update(
        {
            "observation": _observation(
                event, track, "Current smoke and ventilation observation.", [20, 40]
            ),
            "question": "Which mechanism is dominant?",
            "options": None,
            "answer": {"choice": None, "fields": {"mechanism": mechanism}},
            "scoring": {
                "primary": "accuracy",
                "components": ["mechanism"],
                "secondary": ["macro_f1"],
            },
        }
    )
    return row


def build_l3_1(event: dict[str, Any], track: str = "S", split: str = "train") -> dict[str, Any]:
    row = _base(event, "L3-1", track, split)
    labels = _labels(event)
    names = ("temperature_trend", "smoke_trend", "visibility_trend")
    values = {name: labels.get(name) for name in names}
    if any(value not in {"up", "stable", "down"} for value in values.values()):
        raise ValueError("L3-1 needs three deterministic trend labels")
    row.update(
        {
            "observation": _observation(
                event, track, "Current observation and target-region forecast horizon.", [20, 40]
            ),
            "question": "Predict future temperature, smoke, and visibility trends.",
            "options": None,
            "answer": {"choice": None, "fields": values},
            "scoring": {"primary": "mean_accuracy", "components": list(names), "secondary": []},
        }
    )
    return row


def build_l3_2(event: dict[str, Any], track: str = "S", split: str = "train") -> dict[str, Any]:
    row = _base(event, "L3-2", track, split)
    region = _labels(event).get("first_high_risk_region")
    if region not in {*{f"R{index}" for index in range(1, 9)}, "none"}:
        raise ValueError("L3-2 needs a deterministic first_high_risk_region label")
    row.update(
        {
            "observation": _observation(
                event, track, "Current observation and future risk horizon.", [20, 40]
            ),
            "question": "Which region first enters high risk in the prediction window?",
            "options": None,
            "answer": {"choice": None, "fields": {"first_high_risk_region": region}},
            "scoring": {
                "primary": "accuracy",
                "components": ["first_high_risk_region"],
                "secondary": ["event_time_mae"],
            },
        }
    )
    return row


BUILDERS = {
    "L1-1": build_l1_1,
    "L1-2": build_l1_2,
    "L1-3": build_l1_3,
    "L2-1": build_l2_1,
    "L2-2": build_l2_2,
    "L2-3": build_l2_3,
    "L3-1": build_l3_1,
    "L3-2": build_l3_2,
    "L3-3": build_l3_3,
}
