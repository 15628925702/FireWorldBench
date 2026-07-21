"""Canonical machine-readable prediction output contracts."""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from fireworld.contracts import TASKS


def _contract_path() -> Path:
    return Path(__file__).resolve().parents[2] / "configs" / "prediction_contract.v2.json"


@lru_cache(maxsize=1)
def load_prediction_contract() -> dict[str, Any]:
    value = json.loads(_contract_path().read_text(encoding="utf-8"))
    task_contracts = value.get("tasks", {})
    if set(task_contracts) != set(TASKS):
        raise ValueError("prediction contract task IDs do not match frozen TASKS")
    for task_id, task in TASKS.items():
        fields = tuple(task_contracts[task_id].get("answer_fields", {}))
        if fields != task.answer_fields:
            raise ValueError(
                f"{task_id} prediction fields {fields!r} do not match {task.answer_fields!r}"
            )
    return value


def prediction_contract_sha256() -> str:
    return hashlib.sha256(_contract_path().read_bytes()).hexdigest()


def prediction_contract(task_id: str) -> dict[str, Any]:
    return load_prediction_contract()["tasks"][task_id]


def prompt_contract(task_id: str) -> dict[str, Any]:
    contract = load_prediction_contract()
    return {
        "task_id": task_id,
        "model_response_keys": contract["model_response_keys"],
        **contract["tasks"][task_id],
        "choose_one_value_per_field": True,
        "forbidden_extra_fields": True,
    }


def response_json_schema(task_id: str) -> dict[str, Any]:
    task = prediction_contract(task_id)
    choice = {"type": "null"} if task["choice"] is None else {"enum": task["choice"]}
    fields = {
        name: {"enum": values}
        for name, values in task["answer_fields"].items()
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["choice", "fields", "confidence", "evidence"],
        "properties": {
            "choice": choice,
            "fields": {
                "type": "object",
                "additionalProperties": False,
                "required": list(fields),
                "properties": fields,
            },
            "confidence": {
                "anyOf": [
                    {"type": "number", "minimum": 0, "maximum": 1},
                    {"type": "null"},
                ]
            },
            "evidence": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
    }