"""Expert calibration and two-rater agreement utilities without hidden gold access."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from fireworldbench.schema_validation import TASK_LABELS

EXPERT_VERSION = "P3-EXPERT-001"


def validate_annotation(annotation: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    required = ("sample_id", "task", "annotator_id", "label", "evidence", "uncertainty", "status")
    errors.extend(f"missing:{key}" for key in required if key not in annotation)
    task = annotation.get("task")
    if task not in TASK_LABELS:
        errors.append("task_unknown")
    elif annotation.get("label") not in TASK_LABELS[task]:
        errors.append("label_invalid_for_task")
    if not isinstance(annotation.get("evidence"), list):
        errors.append("evidence_must_be_list")
    if annotation.get("status") not in {"independent", "adjudicated", "excluded"}:
        errors.append("status_invalid")
    if annotation.get("annotator_id") in {"gold", "system", "model"}:
        errors.append("annotator_id_reserved")
    return errors


def _kappa(labels_a: Sequence[str], labels_b: Sequence[str]) -> float:
    if not labels_a or len(labels_a) != len(labels_b):
        return 0.0
    observed = sum(a == b for a, b in zip(labels_a, labels_b)) / len(labels_a)
    categories = sorted(set(labels_a) | set(labels_b))
    expected = sum((labels_a.count(category) / len(labels_a)) * (labels_b.count(category) / len(labels_b)) for category in categories)
    return (observed - expected) / (1.0 - expected) if expected < 1.0 else 1.0


def consistency_report(annotations: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    errors = [{"index": index, "errors": validate_annotation(annotation)} for index, annotation in enumerate(annotations)]
    errors = [item for item in errors if item["errors"]]
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for annotation in annotations:
        if not validate_annotation(annotation):
            grouped[str(annotation["sample_id"])].append(annotation)
    paired = [values for values in grouped.values() if len(values) == 2 and values[0]["annotator_id"] != values[1]["annotator_id"]]
    labels_a = [str(values[0]["label"]) for values in paired]
    labels_b = [str(values[1]["label"]) for values in paired]
    evidence_agreement = []
    for values in paired:
        left, right = set(values[0]["evidence"]), set(values[1]["evidence"])
        union = left | right
        evidence_agreement.append(1.0 if not union and not left and not right else (len(left & right) / len(union) if union else 0.0))
    disagreements = [str(values[0]["sample_id"]) for values in paired if values[0]["label"] != values[1]["label"] or set(values[0]["evidence"]) != set(values[1]["evidence"])]
    return {
        "expert_version": EXPERT_VERSION,
        "annotation_count": len(annotations),
        "invalid_annotation_count": len(errors),
        "paired_sample_count": len(paired),
        "label_agreement": (sum(a == b for a, b in zip(labels_a, labels_b)) / len(paired)) if paired else 0.0,
        "cohen_kappa": _kappa(labels_a, labels_b),
        "mean_evidence_jaccard": sum(evidence_agreement) / len(evidence_agreement) if evidence_agreement else 0.0,
        "disagreement_sample_ids": disagreements,
        "adjudication_required": disagreements,
        "errors": errors,
        "expert_gate": "BLOCKED_UNTIL_TWO_DOMAIN_RATERS",
    }


def consistency_file(input_path: Path, output_path: Path) -> dict[str, Any]:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    if isinstance(payload, Mapping):
        annotations = payload.get("annotations", [])
    else:
        annotations = payload
    if not isinstance(annotations, list):
        raise ValueError("annotations must be a list")
    result = consistency_report(annotations)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
