"""Reproducible OpenAI-compatible v2 model runner."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib import request

from fireworld.cli_utils import write_json
from fireworld.contracts import TASKS
from fireworld.validation import read_records, validate_prediction_semantics


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _prompt(qa: dict[str, Any], asset_root: Path, correction: str | None = None) -> str:
    observation = json.loads(json.dumps(qa["observation"]))
    structured = observation.get("structured")
    if structured is not None:
        ref = structured.get("ref")
        asset = (asset_root / str(ref)).resolve()
        root = asset_root.resolve()
        if root not in asset.parents or not asset.is_file():
            raise ValueError(f"unresolvable public structured ref: {ref}")
        structured["content"] = json.loads(asset.read_text(encoding="utf-8"))
    contract = TASKS[qa["task_id"]]
    schema_instruction = {
        "task_id": qa["task_id"],
        "required_answer_fields": list(contract.answer_fields),
        "forbidden_extra_fields": True,
        "choice_allowed": ["A", "B", "C", "D"] if qa["task_id"] == "L1-2" else None,
        "output_shape": {
            "choice": "A/B/C/D or null",
            "fields": {name: "value" for name in contract.answer_fields},
            "confidence": "number 0..1 or null",
            "evidence": "array of strings",
        },
    }
    public = {
        "task_id": qa["task_id"],
        "question": qa["question"],
        "options": qa["options"],
        "observation": observation,
    }
    instruction = (
        "Answer this FireWorldBench item. Return JSON only. "
        "Use exactly the required answer fields below; do not add aliases, explanations, "
        "or any other fields inside answer.fields. The top-level JSON keys must be exactly "
        "schema_version, qa_id, task_id, answer, confidence, evidence. "
        "For L1-2 put the selected option in answer.choice and also fields.choice.\n"
        "REQUIRED OUTPUT CONTRACT:\n" + json.dumps(schema_instruction, sort_keys=True) + "\n"
    )
    if correction:
        instruction += (
            "A previous response failed deterministic validation. Correct it exactly; "
            "do not discuss the correction. Validator errors:\n" + correction + "\n"
        )
    return instruction + json.dumps(public, ensure_ascii=False, sort_keys=True)


def _invoke(base: str, model: str, key: str, prompt: str, timeout_s: float, seed: int) -> dict[str, Any]:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "seed": seed,
        "response_format": {"type": "json_object"},
    }
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        base.rstrip("/") + "/chat/completions",
        data=body,
        method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with request.urlopen(req, timeout=timeout_s) as response:
        return json.loads(response.read().decode("utf-8"))


def _prediction(qa: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    content = response["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    return {
        "schema_version": "2.0.0",
        "qa_id": qa["qa_id"],
        "task_id": qa["task_id"],
        "answer": {"choice": parsed.get("choice"), "fields": parsed.get("fields", {})},
        "confidence": parsed.get("confidence"),
        "evidence": parsed.get("evidence", []),
    }


def run(
    qa_path: Path, output: Path, model: str, track: str, base: str,
    key_env: str, seed: int, timeout_s: float, retries: int, allow_network: bool,
) -> dict[str, Any]:
    rows = [row for row in read_records(qa_path) if row.get("track") == track]
    asset_root = qa_path.parent
    if not rows:
        raise ValueError(f"no {track}-track rows in {qa_path}")
    if any(row.get("split") in {"train", "dev"} for row in rows):
        raise ValueError("runner rejects train/dev inputs")
    if any(row.get("answer") != {"choice": None, "fields": {}} for row in rows):
        raise ValueError("runner requires redacted public answers")
    output.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": "2.0.0", "runner_version": "0.2.0", "model": model,
        "track": track, "api_base": base, "seed": seed, "timeout_s": timeout_s,
        "max_retries": retries, "qa_count": len(rows), "qa_sha256": _sha256(json.dumps(rows, sort_keys=True)),
        "credential_env": key_env, "network_enabled": allow_network,
        "created_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "validation_repair_prompt": True,
    }
    write_json(manifest, output / "run_manifest.json")
    if not allow_network:
        write_json([], output / "predictions.json")
        write_json([], output / "failures.json")
        return {"status": "dry_run", "qa_count": len(rows)}
    key = os.environ.get(key_env)
    if not key:
        raise ValueError(f"missing credential environment variable: {key_env}")
    predictions, raw, failures = [], [], []
    for qa in rows:
        correction = None
        for attempt in range(retries + 1):
            try:
                response = _invoke(base, model, key, _prompt(qa, asset_root, correction), timeout_s, seed)
                prediction = _prediction(qa, response)
                errors = validate_prediction_semantics(prediction, qa)
                if errors:
                    correction = "; ".join(errors)
                    raise ValueError(correction)
                predictions.append(prediction)
                raw.append({"qa_id": qa["qa_id"], "response": response, "attempt": attempt + 1})
                break
            except Exception as exc:
                correction = str(exc)
                if attempt == retries:
                    failures.append({"qa_id": qa["qa_id"], "attempts": attempt + 1, "error": correction})
    write_json(predictions, output / "predictions.json")
    write_json(raw, output / "raw_responses.json")
    write_json(failures, output / "failures.json")
    return {"status": "complete", "qa_count": len(rows), "predictions": len(predictions), "failures": len(failures)}
