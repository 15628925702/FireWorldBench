"""Strict release-native deterministic baselines."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from fireworld.cli_utils import write_json
from fireworld.prediction_contracts import prediction_contract
from fireworld.scoring import aggregate_scores
from fireworld.validation import read_records, validate_prediction_semantics, validate_schema


def predict(qa: dict[str, Any], choice: str | None, fields: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "2.0.0", "qa_id": qa["qa_id"], "task_id": qa["task_id"],
        "answer": {"choice": choice, "fields": fields}, "confidence": None, "evidence": [],
    }


def asset(root: Path, ref: str) -> dict[str, Any]:
    value = (root.resolve() / ref).resolve()
    if root.resolve() not in value.parents or not value.is_file():
        raise ValueError(f"unresolvable public asset ref: {ref}")
    return json.loads(value.read_text(encoding="utf-8"))


def chance(qa: dict[str, Any], seed: int) -> dict[str, Any]:
    contract = prediction_contract(qa["task_id"])

    def pick(name: str, values: list[Any]) -> Any:
        digest = hashlib.sha256(f"{seed}:{qa['qa_id']}:{name}".encode()).digest()
        return values[int.from_bytes(digest[:8], "big") % len(values)]

    fields = {name: pick(name, values) for name, values in contract["answer_fields"].items()}
    choice = None if contract["choice"] is None else pick("choice", contract["choice"])
    if qa["task_id"] == "L1-2":
        fields["choice"] = choice
    if qa["task_id"] == "L1-3":
        if fields["consistency"] == "consistent":
            fields["violation_type"] = None
        elif fields["violation_type"] is None:
            fields["violation_type"] = pick(
                "violation_type_nonnull",
                [item for item in contract["answer_fields"]["violation_type"] if item is not None],
            )
    return predict(qa, choice, fields)


def majorities(train: list[dict[str, Any]]) -> dict[tuple[str, str], tuple[str | None, dict[str, Any]]]:
    buckets: dict[tuple[str, str], Counter[tuple[str | None, str]]] = {}
    for row in train:
        key = (row["track"], row["task_id"])
        answer = row["answer"]
        item = (answer["choice"], json.dumps(answer["fields"], sort_keys=True))
        buckets.setdefault(key, Counter())[item] += 1
    result = {}
    for key, count in buckets.items():
        winner = min(count, key=lambda item: (-count[item], item[1], str(item[0])))
        result[key] = winner[0], json.loads(winner[1])
    return result


def value(row: dict[str, Any], prefix: str, region: int, default: float) -> float:
    for key in (f"{prefix}_R{region}", f"{prefix}_R{region}_CEILING"):
        if isinstance(row.get(key), (int, float)):
            return float(row[key])
    return default


def rule(qa: dict[str, Any], root: Path) -> dict[str, Any]:
    if qa["track"] != "S":
        raise ValueError("physical_rule requires S structured input")
    data = asset(root, qa["observation"]["structured"]["ref"])
    rows = [row for row in data.get("rows", []) if isinstance(row, dict)]
    last = rows[-1] if rows else {}
    task = qa["task_id"]

    if task == "L1-1":
        temperatures = [float(v) for row in rows for k, v in row.items() if k.startswith("T_") and isinstance(v, (int, float))]
        velocity = [abs(float(v)) for row in rows for k, v in row.items() if k.startswith("U_") and isinstance(v, (int, float))]
        label = "fire" if max(temperatures, default=20) > 24 else "ventilation_disturbance" if max(velocity, default=0) > .8 else "no_fire"
        return predict(qa, None, {"class": label})
    if task == "L1-2":
        current = last
        keys = [key for key in current if key.startswith(("T_", "V_"))]
        candidates = []
        for option in qa.get("options") or []:
            state = asset(root, option["content_ref"])["values"]
            distance = sum((float(state.get(key, 0))-float(current.get(key, 0)))**2 for key in keys)
            candidates.append((distance, option["id"]))
        choice = min(candidates)[1]
        return predict(qa, choice, {"choice": choice})
    if task == "L1-3":
        return predict(qa, None, {"consistency": "consistent", "violation_type": None})

    scores = {f"R{i}": max((value(last, "T", i, 20)-20)/40, (30-value(last, "V", i, 30))/6) for i in range(1, 9)}
    region = max(scores, key=scores.__getitem__)
    if task == "L2-1":
        maximum = max(value(last, "T", i, 20) for i in range(1, 9))
        stage = "incipient" if maximum < 25 else "growth" if maximum < 80 else "developed"
        return predict(qa, None, {"source_region": region, "stage": stage})
    if task == "L2-2":
        number = int(region[1:]); temp = value(last, "T", number, 20); visibility = value(last, "V", number, 30)
        level = "critical" if temp >= 200 or visibility <= 3 else "high" if temp >= 60 or visibility <= 10 else "moderate" if temp >= 35 or visibility <= 20 else "low"
        return predict(qa, None, {"risk_region": region, "risk_level": level})
    if task == "L2-3":
        speed = max((abs(float(v)) for k, v in last.items() if k.startswith("U_") and isinstance(v, (int, float))), default=0)
        return predict(qa, None, {"mechanism": "longitudinal_ventilation" if speed > 1 else "smoke_layer"})
    if task == "L3-1":
        first = rows[0]
        def trend(name: str, deadband: float, inverse: bool = False) -> str:
            delta = float(last[name])-float(first[name])
            return "stable" if abs(delta) < deadband else "down" if (delta < 0) ^ inverse else "up"
        return predict(qa, None, {"temperature_trend": trend("temperature_c", 5), "smoke_trend": trend("soot_density_kg_m3", 1e-7), "visibility_trend": trend("visibility_m", 1, True)})
    if task == "L3-2":
        high = [f"R{i}" for i in range(1, 9) if value(last, "T", i, 20) >= 55 or value(last, "V", i, 30) <= 11]
        return predict(qa, None, {"first_high_risk_region": high[0] if high else "none"})
    left, right = data.get("A", []), data.get("B", [])
    a = max((float(v) for k, v in left[-1].items() if k.startswith("T_")), default=20)
    b = max((float(v) for k, v in right[-1].items() if k.startswith("T_")), default=20)
    return predict(qa, None, {"comparison": "A" if a > b+1 else "B" if b > a+1 else "same"})


def validate(rows: list[dict[str, Any]]) -> None:
    errors = [error for row in rows for error in validate_schema(row, "prediction.v2.schema.json") + validate_prediction_semantics(row)]
    if errors:
        raise ValueError("; ".join(errors[:20]))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--track", choices=("S", "I"), required=True)
    parser.add_argument("--gold", type=Path)
    parser.add_argument("--seed", type=int, default=20260720)
    args = parser.parse_args()
    public = args.release.resolve() / "public"
    train = [row for row in read_records(public / "qa_train_dev.json") if row["split"] == "train" and row["track"] == args.track]
    test = [row for row in read_records(public / "qa_test_questions.json") if row["track"] == args.track]
    modes = majorities(train)
    if any((row["track"], row["task_id"]) not in modes for row in test):
        raise ValueError("train does not cover every test task")
    methods: dict[str, list[dict[str, Any]] | str] = {
        "seeded_chance": [chance(row, args.seed) for row in test],
        "train_majority": [predict(row, *modes[(row["track"], row["task_id"])]) for row in test],
        "physical_rule": [rule(row, public) for row in test] if args.track == "S" else "unsupported: no structured S input",
    }
    gold = read_records(args.gold) if args.gold else None
    args.output.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {"schema_version": "2.0.0", "track": args.track, "seed": args.seed, "train_rows": len(train), "test_rows": len(test), "methods": {}, "llm_judge_used": False}
    for name, result in methods.items():
        if isinstance(result, str):
            report["methods"][name] = {"status": result}; continue
        validate(result); write_json(result, args.output / f"{name}_predictions.json")
        status: dict[str, Any] = {"status": "complete", "predictions": len(result)}
        if gold:
            status["score"] = aggregate_scores(gold, {row["qa_id"]: row for row in result}, partition=None, track=args.track)
            write_json(status["score"], args.output / f"{name}_score.json")
        report["methods"][name] = status
    write_json(report, args.output / "baseline_report.json")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())