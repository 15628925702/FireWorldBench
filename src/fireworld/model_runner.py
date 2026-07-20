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
from fireworld.validation import read_records, validate_prediction_semantics


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _prompt(qa: dict[str, Any]) -> str:
    public = {
        "task_id": qa["task_id"],
        "question": qa["question"],
        "options": qa["options"],
        "observation": qa["observation"],
    }
    instruction = (
        "Answer this FireWorldBench item. Return JSON only with choice, fields, "
        "confidence, and evidence. Do not use information outside the item.\n"
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
    if not rows:
        raise ValueError(f"no {track}-track rows in {qa_path}")
    if any(row.get("split") in {"train", "dev"} for row in rows):
        raise ValueError("runner rejects train/dev inputs")
    if any(row.get("answer") != {"choice": None, "fields": {}} for row in rows):
        raise ValueError("runner requires redacted public answers")
    output.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": "2.0.0", "runner_version": "0.1.0", "model": model,
        "track": track, "api_base": base, "seed": seed, "timeout_s": timeout_s,
        "max_retries": retries, "qa_count": len(rows), "qa_sha256": _sha256(json.dumps(rows, sort_keys=True)),
        "credential_env": key_env, "network_enabled": allow_network,
        "created_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
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
        for attempt in range(retries + 1):
            try:
                response = _invoke(base, model, key, _prompt(qa), timeout_s, seed)
                prediction = _prediction(qa, response)
                errors = validate_prediction_semantics(prediction, qa)
                if errors:
                    raise ValueError("; ".join(errors))
                predictions.append(prediction)
                raw.append({"qa_id": qa["qa_id"], "response": response})
                break
            except Exception as exc:
                if attempt == retries:
                    failures.append({"qa_id": qa["qa_id"], "attempts": attempt + 1, "error": str(exc)})
    write_json(predictions, output / "predictions.json")
    write_json(raw, output / "raw_responses.json")
    write_json(failures, output / "failures.json")
    return {"status": "complete", "qa_count": len(rows), "predictions": len(predictions), "failures": len(failures)}
