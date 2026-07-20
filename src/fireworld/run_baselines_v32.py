"""Run non-oracle v3.2 baselines and a separately marked scorer self-check."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from itertools import pairwise
from pathlib import Path
from typing import Any, cast

from fireworld.mini_pilot import write_json
from fireworld.scoring import aggregate_scores

TEST_SPLITS = {"test_iid", "test_ood_geometry", "test_ood_condition", "test_ood_view_sensor"}


def key(item: dict[str, Any]) -> tuple[str | None, tuple[tuple[str, Any], ...]]:
    return item["answer"]["choice"], tuple(sorted(item["answer"]["fields"].items()))


def prediction(item: dict[str, Any], choice: str | None, fields: dict[str, Any]) -> dict[str, Any]:
    return {"qa_id": item["qa_id"], "answer": {"choice": choice, "fields": fields}}


def payload(root: Path, item: dict[str, Any]) -> dict[str, Any]:
    structured = item["observation"]["structured"]
    return json.loads((root / structured["ref"]).read_text()) if structured else {}


def rows(value: dict[str, Any]) -> list[dict[str, float]]:
    return [row for row in value.get("rows", []) if isinstance(row, dict)]


def rule(root: Path, item: dict[str, Any]) -> dict[str, Any]:
    task = item["task_id"]
    data = payload(root, item)
    values = rows(data)
    if task == "L1-1":
        temperatures = [[float(v) for k, v in row.items() if k.startswith("T_")] for row in values]
        velocities = [abs(float(v)) for row in values for k, v in row.items() if k.startswith("U_")]
        jumps = (
            [
                abs(b - a)
                for series in zip(*temperatures, strict=True)
                for a, b in pairwise(series)
            ]
            if temperatures
            else []
        )
        label = "sensor_fault" if max(jumps, default=0.0) > 15 else "fire" if max((v for row in temperatures for v in row), default=20) > 24 else "ventilation_disturbance" if max(velocities, default=0) > 0.8 else "no_fire"
        return prediction(item, None, {"class": label})
    if task == "L1-2":
        current = values[-1] if values else {}
        candidates: list[tuple[str, dict[str, Any]]] = [
            (
                str(option["id"]),
                cast(
                    dict[str, Any],
                    payload(
                        root,
                        {
                            "observation": {
                                "structured": {"ref": option["content_ref"]}
                            }
                        },
                    )["values"],
                ),
            )
            for option in item["options"]
        ]
        fields = [key for key in current if key.startswith(("T_", "V_"))]

        def distance(candidate: dict[str, Any]) -> float:
            return sum(
                (float(candidate.get(name, 0)) - float(current.get(name, 0))) ** 2
                for name in fields
            )

        choice = min(candidates, key=lambda pair: distance(pair[1]))[0]
        return prediction(item, choice, {"choice": choice})
    if task == "L1-3":
        return prediction(item, None, {"consistency": "consistent", "violation_type": None})
    if task in {"L2-1", "L2-2"}:
        row = values[-1] if values else {}
        scores = {f"R{i}": max((float(row.get(f"T_R{i}", 20)) - 20) / 40, (30 - float(row.get(f"V_R{i}", 30))) / 6) for i in range(1, 9)}
        region = max(scores, key=scores.__getitem__)
        if task == "L2-1":
            maximum = max(float(row.get(f"T_R{i}", 20)) for i in range(1, 9))
            stage = "incipient" if maximum < 25 else "growth" if maximum < 80 else "developed"
            return prediction(item, None, {"source_region": region, "stage": stage})
        temp, vis = float(row.get(f"T_{region}", 20)), float(row.get(f"V_{region}", 30))
        level = "critical" if temp >= 200 or vis <= 3 else "high" if temp >= 60 or vis <= 10 else "moderate" if temp >= 35 or vis <= 20 else "low"
        return prediction(item, None, {"risk_region": region, "risk_level": level})
    if task == "L2-3":
        row = values[-1] if values else {}
        speed = max((abs(float(value)) for name, value in row.items() if name.startswith("U_")), default=0)
        mechanism = "longitudinal_ventilation" if speed > 1 else "smoke_layer"
        return prediction(item, None, {"mechanism": mechanism})
    if task == "L3-1":
        first, last = values[0], values[-1]
        def direction(name: str, deadband: float, inverse: bool = False) -> str:
            delta = float(last[name]) - float(first[name])
            return "stable" if abs(delta) < deadband else "down" if (delta < 0) ^ inverse else "up"
        return prediction(item, None, {"temperature_trend": direction("temperature_c", 5), "smoke_trend": direction("soot_density_kg_m3", 1e-7), "visibility_trend": direction("visibility_m", 1, True)})
    if task == "L3-2":
        row = values[-1] if values else {}
        regions = [f"R{i}" for i in range(1, 9) if float(row.get(f"T_R{i}", 20)) >= 55 or float(row.get(f"V_R{i}", 30)) <= 11]
        return prediction(item, None, {"first_high_risk_region": regions[0] if regions else "none"})
    pair = data
    left = pair.get("A", pair.get("A_current_rows", []))
    right = pair.get("B", pair.get("B_current_rows", []))
    a = max((float(v) for k, v in left[-1].items() if k.startswith("T_R")), default=20) if left else 20
    b = max((float(v) for k, v in right[-1].items() if k.startswith("T_R")), default=20) if right else 20
    comparison = "A" if a > b + 1 else "B" if b > a + 1 else "same"
    return prediction(item, None, {"comparison": comparison})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    qa: list[dict[str, Any]] = json.loads((root / "qa/fds_core_v3_2/qa.json").read_text())
    qa = [item for item in qa if item["quality"]["status"] in {"eligible", "eligible_expert_review_deferred"}]
    train = [item for item in qa if item["split"] == "train"]
    test = [item for item in qa if item["split"] in TEST_SPLITS]
    majority: dict[str, tuple[str | None, dict[str, Any]]] = {}
    for task in {item["task_id"] for item in train}:
        winner = Counter(key(item) for item in train if item["task_id"] == task).most_common(1)[0][0]
        majority[task] = winner[0], dict(winner[1])
    majority_predictions = {item["qa_id"]: prediction(item, *majority[item["task_id"]]) for item in test}
    rule_predictions = {item["qa_id"]: rule(root, item) for item in test}
    oracle_predictions = {item["qa_id"]: prediction(item, item["answer"]["choice"], item["answer"]["fields"]) for item in test}
    chance = {"L1-1": 25.0, "L1-2": 25.0, "L1-3": 50.0, "L2-1": 3.125, "L2-2": 3.125, "L2-3": 100 / 6, "L3-1": 100 / 27, "L3-2": 100 / 9, "L3-3": 100 / 3}
    for name, predictions in (("majority", majority_predictions), ("physical_rule", rule_predictions), ("oracle_self_check", oracle_predictions)):
        write_json(root / "reports" / f"fds_core_v3_2_{name}_predictions.json", list(predictions.values()))
    report = {"schema_version": "fds-core-v3.2.0", "test_rows": len(test), "chance_task_scores": chance, "chance_overall": sum(chance.values()) / 9, "train_majority": aggregate_scores(test, majority_predictions), "physical_rule": aggregate_scores(test, rule_predictions), "oracle_self_check_excluded_from_results": aggregate_scores(test, oracle_predictions), "llm_judge_used": False, "external_mllm_results": "not_run_no_credentials_or_model_runtime"}
    write_json(root / "reports/fds_core_v3_2_baselines.json", report)
    print(json.dumps(report, indent=2))
    score_names = (
        "train_majority",
        "physical_rule",
        "oracle_self_check_excluded_from_results",
    )
    score_reports = [cast(dict[str, Any], report[name]) for name in score_names]
    oracle = cast(dict[str, Any], report["oracle_self_check_excluded_from_results"])
    return (
        0
        if all(score_report["overall"] is not None for score_report in score_reports)
        and oracle["overall"] == 100.0
        else 2
    )


if __name__ == "__main__":
    raise SystemExit(main())
