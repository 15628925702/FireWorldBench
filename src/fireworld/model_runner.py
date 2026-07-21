"""Reproducible OpenAI-compatible v2 model runner."""

from __future__ import annotations

import base64
import hashlib
import json
import mimetypes
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib import error, request

from fireworld.cli_utils import write_json
from fireworld.prediction_contracts import (
    prediction_contract_sha256,
    prompt_contract,
    response_json_schema,
)
from fireworld.validation import read_records, validate_prediction_semantics, validate_schema

INPUT_ADAPTERS = {
    "S": "structured_json_and_candidate_hydration_v1",
    "I": "openai_image_url_data_v1",
    "V": "unsupported_without_declared_video_input_v1",
}


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _resolve_asset(asset_root: Path, ref: str) -> Path:
    root = asset_root.resolve()
    asset = (root / ref).resolve()
    if root not in asset.parents or not asset.is_file():
        raise ValueError(f"unresolvable public asset ref: {ref}")
    return asset


def _structured_content(asset_root: Path, ref: str) -> dict[str, Any]:
    return json.loads(_resolve_asset(asset_root, ref).read_text(encoding="utf-8"))


def _image_part(asset_root: Path, ref: str) -> dict[str, Any]:
    asset = _resolve_asset(asset_root, ref)
    mime, _ = mimetypes.guess_type(asset.name)
    if mime not in {"image/jpeg", "image/png", "image/webp"}:
        raise ValueError(f"unsupported image MIME type for I track: {asset.name}")
    encoded = base64.b64encode(asset.read_bytes()).decode("ascii")
    return {
        "type": "image_url",
        "image_url": {"url": f"data:{mime};base64,{encoded}", "detail": "high"},
    }


def _hydrate_structured(
    qa: dict[str, Any], asset_root: Path
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    observation = json.loads(json.dumps(qa["observation"]))
    options = json.loads(json.dumps(qa.get("options") or []))
    structured = observation.get("structured")
    if structured is None:
        raise ValueError("S track requires observation.structured")
    structured["content"] = _structured_content(asset_root, structured["ref"])
    for option in options:
        ref = option.get("content_ref")
        if ref is not None:
            option["content"] = _structured_content(asset_root, ref)
    return observation, options


def _prompt(
    qa: dict[str, Any], asset_root: Path, correction: str | None = None
) -> str | list[dict[str, Any]]:
    track = qa["track"]
    if track == "V":
        raise ValueError(
            "V track is unsupported for this fixed model: provider declares no video input modality"
        )
    schema_instruction = prompt_contract(qa["task_id"])
    if track == "S":
        observation, options = _hydrate_structured(qa, asset_root)
        public = {
            "task_id": qa["task_id"],
            "question": qa["question"],
            "options": options,
            "observation": observation,
        }
    elif track == "I":
        image_refs = qa["observation"].get("images")
        if not isinstance(image_refs, list) or not image_refs:
            raise ValueError("I track requires one or more observation images")
        options = json.loads(json.dumps(qa.get("options") or []))
        public = {
            "task_id": qa["task_id"],
            "question": qa["question"],
            "options": [
                {key: value for key, value in option.items() if key != "content_ref"}
                for option in options
            ],
            "observation": {
                "image_count": len(image_refs),
                "context": qa["observation"].get("context"),
                "time_window_s": qa["observation"].get("time_window_s"),
            },
        }
    else:
        raise ValueError(f"unknown track: {track}")
    instruction = (
        "Answer this FireWorldBench item using the enforced JSON response schema. "
        "Choose exactly one allowed value for each field; enum arrays describe allowed "
        "choices and must never be copied as field values. Do not add aliases or explanations. "
        "The runner binds schema_version, qa_id, and task_id from the frozen public QA input; "
        "do not output them.\nMODEL RESPONSE CONTRACT:\n"
        + json.dumps(schema_instruction, sort_keys=True)
        + "\n"
    )
    if correction:
        instruction += (
            "A previous response failed deterministic validation. Correct it exactly; "
            "do not discuss the correction. Validator errors:\n" + correction + "\n"
        )
    text = instruction + json.dumps(public, ensure_ascii=False, sort_keys=True)
    if track == "S":
        return text

    content: list[dict[str, Any]] = [{"type": "text", "text": text}]
    for index, ref in enumerate(image_refs, start=1):
        content.append({"type": "text", "text": f"Observation frame {index} of {len(image_refs)}."})
        content.append(_image_part(asset_root, ref))
    for option in options:
        ref = option.get("content_ref")
        if ref is None:
            continue
        content.append({"type": "text", "text": f"Candidate option {option['id']} image."})
        content.append(_image_part(asset_root, ref))
    return content


def _invoke(
    base: str, model: str, key: str, prompt: str | list[dict[str, Any]],
    timeout_s: float, seed: int, schema: dict[str, Any],
) -> dict[str, Any]:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "seed": seed,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "fireworld_prediction",
                "strict": True,
                "schema": schema,
            },
        },
    }
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        base.rstrip("/") + "/chat/completions",
        data=body,
        method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with request.urlopen(req, timeout=timeout_s) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail[:2000]}") from exc


def _prediction(qa: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    content = response["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    if not isinstance(parsed, dict):
        raise ValueError("model response must be a JSON object")
    expected = {"choice", "fields", "confidence", "evidence"}
    if set(parsed) != expected:
        raise ValueError(
            f"model response keys must be exactly {sorted(expected)}; got {sorted(parsed)}"
        )
    return {
        "schema_version": "2.0.0",
        "qa_id": qa["qa_id"],
        "task_id": qa["task_id"],
        "answer": {"choice": parsed["choice"], "fields": parsed["fields"]},
        "confidence": parsed["confidence"],
        "evidence": parsed["evidence"],
    }


def _checkpoint(
    output: Path, predictions: list[dict[str, Any]], raw: list[dict[str, Any]],
    failures: list[dict[str, Any]], processed: int, total: int,
) -> None:
    for name, value in (
        ("predictions.json", predictions),
        ("raw_responses.json", raw),
        ("failures.json", failures),
    ):
        temporary = output / f".{name}.tmp"
        write_json(value, temporary)
        temporary.replace(output / name)
    write_json(
        {
            "processed": processed,
            "total": total,
            "predictions": len(predictions),
            "failures": len(failures),
            "status": "complete" if processed == total else "running",
        },
        output / "progress.json",
    )


def run(
    qa_path: Path, output: Path, model: str, track: str, base: str,
    key_env: str, seed: int, timeout_s: float, retries: int, allow_network: bool,
    asset_root: Path | None = None,
) -> dict[str, Any]:
    rows = [row for row in read_records(qa_path) if row.get("track") == track]
    asset_root = (asset_root or qa_path.parent).resolve()
    if track not in INPUT_ADAPTERS:
        raise ValueError(f"unknown track: {track}")
    if track == "V":
        raise ValueError(
            "V track unsupported for this fixed model; use a model with declared video input modality"
        )
    if not rows:
        raise ValueError(f"no {track}-track rows in {qa_path}")
    if any(row.get("split") in {"train", "dev"} for row in rows):
        raise ValueError("runner rejects train/dev inputs")
    if any(row.get("answer") != {"choice": None, "fields": {}} for row in rows):
        raise ValueError("runner requires redacted public answers")
    output.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": "2.0.0",
        "runner_version": "0.5.0",
        "model": model,
        "track": track,
        "input_adapter": INPUT_ADAPTERS[track],
        "api_base": base,
        "seed": seed,
        "timeout_s": timeout_s,
        "max_retries": retries,
        "qa_count": len(rows),
        "qa_sha256": _sha256(json.dumps(rows, sort_keys=True)),
        "credential_env": key_env,
        "network_enabled": allow_network,
        "created_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "validation_repair_prompt": True,
        "prediction_contract_sha256": prediction_contract_sha256(),
        "asset_root": str(asset_root),
    }
    write_json(manifest, output / "run_manifest.json")
    if not allow_network:
        _checkpoint(output, [], [], [], 0, len(rows))
        return {"status": "dry_run", "qa_count": len(rows)}
    key = os.environ.get(key_env)
    if not key:
        raise ValueError(f"missing credential environment variable: {key_env}")
    predictions, raw, failures = [], [], []
    for index, qa in enumerate(rows, start=1):
        correction = None
        for attempt in range(retries + 1):
            try:
                response = _invoke(
                    base, model, key, _prompt(qa, asset_root, correction),
                    timeout_s, seed, response_json_schema(qa["task_id"]),
                )
                raw.append({"qa_id": qa["qa_id"], "response": response, "attempt": attempt + 1})
                prediction = _prediction(qa, response)
                errors = validate_schema(
                    prediction, "prediction.v2.schema.json"
                ) + validate_prediction_semantics(prediction, qa)
                if errors:
                    correction = "; ".join(errors)
                    raise ValueError(correction)
                predictions.append(prediction)
                break
            except Exception as exc:
                correction = str(exc)
                if attempt == retries:
                    failures.append({"qa_id": qa["qa_id"], "attempts": attempt + 1, "error": correction})
        if index % 25 == 0:
            _checkpoint(output, predictions, raw, failures, index, len(rows))
    _checkpoint(output, predictions, raw, failures, len(rows), len(rows))
    return {
        "status": "complete",
        "qa_count": len(rows),
        "predictions": len(predictions),
        "failures": len(failures),
    }