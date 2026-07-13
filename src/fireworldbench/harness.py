"""Deterministic train/dev-only model harness with isolated raw responses."""

from __future__ import annotations

import hashlib
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

HARNESS_VERSION = "P4-HARNESS-001"
ALLOWED_SPLITS = {"train_id", "dev_id"}
Adapter = Callable[[Mapping[str, Any], str, Mapping[str, Any]], Any]


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _mock_adapter(sample: Mapping[str, Any], prompt: str, config: Mapping[str, Any]) -> dict[str, Any]:
    return {"schema_version": "2.0", "sample_id": sample["sample_id"], "task": sample["task"], "answer": {"label": "insufficient_information"}, "evidence": [], "uncertainty": {"level": "unknown", "reason": "mock adapter"}, "missing_information": ["model_not_configured"]}


def run_harness(samples: Sequence[Mapping[str, Any]], output_root: Path, *, adapter: Adapter | None = None, prompt_template: str = "Answer the task using only supplied observations.", config: Mapping[str, Any] | None = None, max_retries: int = 0, timeout_s: float = 30.0) -> dict[str, Any]:
    config = dict(config or {"adapter": "mock", "max_retries": max_retries, "timeout_s": timeout_s})
    if os.environ.get("FIREWORLDBENCH_PRIVATE_ROOT"):
        raise PermissionError("ordinary harness cannot mount FIREWORLDBENCH_PRIVATE_ROOT")
    if output_root.exists():
        raise FileExistsError(f"run output already exists: {output_root}")
    if any(sample.get("split") not in ALLOWED_SPLITS for sample in samples):
        raise ValueError("harness only permits train_id or dev_id")
    adapter = adapter or _mock_adapter
    prompt_hash = _hash(prompt_template)
    config_hash = _hash(config)
    run_id = "run_" + _hash({"sample_ids": [sample.get("sample_id") for sample in samples], "prompt_hash": prompt_hash, "config_hash": config_hash})[:16]
    public_root = output_root / "public"
    private_root = output_root / "private"
    public_root.mkdir(parents=True)
    private_root.mkdir(parents=True)
    results: list[dict[str, Any]] = []
    raw_lines: list[str] = []
    for sample in sorted(samples, key=lambda item: str(item.get("sample_id", ""))):
        sample_id = str(sample["sample_id"])
        prompt = prompt_template.format(task=sample.get("task", ""), sample_id=sample_id)
        status = "tool_error"
        parsed: dict[str, Any] | None = None
        raw_response: Any = None
        attempts = 0
        started = time.perf_counter()
        error = None
        for attempt in range(max_retries + 1):
            attempts = attempt + 1
            try:
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(adapter, sample, prompt, config)
                    raw_response = future.result(timeout=timeout_s)
                if isinstance(raw_response, Mapping):
                    parsed = dict(raw_response)
                elif isinstance(raw_response, str):
                    parsed_value = json.loads(raw_response)
                    parsed = dict(parsed_value) if isinstance(parsed_value, Mapping) else None
                if parsed is None:
                    status = "invalid_json"
                    error = "adapter response is not an object"
                    if attempt < max_retries:
                        continue
                else:
                    status = "refusal" if parsed.get("answer", {}).get("label") in {"refusal", "insufficient_information"} else "ok"
                break
            except TimeoutError:
                status, error = "timeout", f"timeout after {timeout_s}s"
                if attempt < max_retries:
                    continue
            except json.JSONDecodeError as exc:
                status, error = "invalid_json", str(exc)
                if attempt < max_retries:
                    continue
            except Exception as exc:  # adapter boundary must retain tool failures
                status, error = "tool_error", f"{type(exc).__name__}: {exc}"
                if attempt < max_retries:
                    continue
            break
        latency_ms = round((time.perf_counter() - started) * 1000, 3)
        raw_entry = {"sample_id": sample_id, "status": status, "attempts": attempts, "raw_response": raw_response, "error": error}
        raw_lines.append(json.dumps(raw_entry, ensure_ascii=False, sort_keys=True))
        public_result = {"sample_id": sample_id, "task": sample.get("task"), "split": sample.get("split"), "status": status, "attempts": attempts, "latency_ms": latency_ms, "prompt_hash": prompt_hash, "config_hash": config_hash, "raw_response_ref": f"private/raw_responses.jsonl#{len(raw_lines)}"}
        results.append(public_result)
    (private_root / "raw_responses.jsonl").write_text("\n".join(raw_lines) + "\n", encoding="utf-8")
    public_manifest = {"harness_version": HARNESS_VERSION, "run_id": run_id, "sample_count": len(results), "prompt_hash": prompt_hash, "config_hash": config_hash, "results": results, "private_raw_response": True, "test_split": False}
    (public_root / "run_manifest.json").write_text(json.dumps(public_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    private_manifest = {"harness_version": HARNESS_VERSION, "run_id": run_id, "raw_response_path": "raw_responses.jsonl", "raw_response_count": len(raw_lines), "public_manifest_hash": _hash(public_manifest), "test_gold_read": False}
    (private_root / "private_manifest.json").write_text(json.dumps(private_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return public_manifest
