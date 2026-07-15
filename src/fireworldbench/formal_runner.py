"""Guarded formal-main probe and execution helpers."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from fireworldbench.deepseek import openai_compatible_adapter
from fireworldbench.formal_readiness import READY_STATUS
from fireworldbench.llm_baseline import LLMConfig, PROMPT_REGISTRY, _normalise_prediction, _render_prompt, run_llm_pilot
from fireworldbench.schema_validation import validate_prediction
from fireworldbench.scorer import score_samples

FORMAL_RUNNER_VERSION = "P5-MAIN-001-RUNNER-v1"
FORMAL_ALLOWED_SPLITS = {"train_id", "dev_id", "test_id", "test_ood", "external_test"}
PROBE_ALLOWED_SPLITS = {"train_id", "dev_id"}
Adapter = Callable[[Mapping[str, Any], str, Mapping[str, Any]], Any]


def _hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _load_samples(samples_path: Path) -> list[Mapping[str, Any]]:
    payload = json.loads(samples_path.read_text(encoding="utf-8-sig"))
    value = payload.get("samples", payload) if isinstance(payload, Mapping) else payload
    if not isinstance(value, list):
        raise TypeError("formal runner samples must be a JSON list or an object with a samples list")
    return value


def _load_mapping(path: Path, label: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, Mapping):
        raise TypeError(f"{label} must be a JSON object")
    return dict(payload)


def _parse_response(raw: Any) -> dict[str, Any] | None:
    if isinstance(raw, Mapping):
        return dict(raw)
    if isinstance(raw, str):
        parsed = json.loads(raw)
        return dict(parsed) if isinstance(parsed, Mapping) else None
    return None


def _git_head(root: Path) -> str:
    try:
        return (
            subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError("unable to resolve clean git HEAD for formal runner") from exc


def _ensure_clean_git(root: Path) -> str:
    head = _git_head(root)
    status = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if status:
        raise RuntimeError("formal runner requires a clean git worktree")
    return head


@dataclass(frozen=True)
class ExecutableModelSpec:
    model_id: str
    provider: str
    endpoint_or_checkpoint: str
    prompt_id: str
    max_input_tokens: int
    max_output_tokens: int
    temperature: float
    top_p: float
    max_retries: int
    timeout_s: float
    budget_usd: float
    input_usd_per_1k_tokens: float
    output_usd_per_1k_tokens: float
    adapter_kind: str
    credential_env: str
    approval_status: str

    def llm_config(self) -> LLMConfig:
        return LLMConfig(
            track="text_only_table",
            prompt_id=self.prompt_id,
            model_id=self.model_id,
            approved=True,
            repeats=1,
            temperature=self.temperature,
            top_p=self.top_p,
            max_input_tokens=self.max_input_tokens,
            max_output_tokens=self.max_output_tokens,
            max_retries=self.max_retries,
            timeout_s=self.timeout_s,
            max_cost_usd=self.budget_usd,
            input_usd_per_1k_tokens=self.input_usd_per_1k_tokens,
            output_usd_per_1k_tokens=self.output_usd_per_1k_tokens,
        )


def resolve_model_spec(
    model_matrix_path: Path,
    model_id: str,
    *,
    allow_unapproved: bool = False,
) -> ExecutableModelSpec:
    matrix = _load_mapping(model_matrix_path, "model matrix")
    models = matrix.get("models", [])
    if not isinstance(models, list):
        raise TypeError("model matrix models must be a list")
    match = next(
        (
            item
            for item in models
            if isinstance(item, Mapping) and str(item.get("model_id")) == model_id
        ),
        None,
    )
    if match is None:
        raise KeyError(f"model_id not found in model matrix: {model_id}")
    approval_status = str(match.get("approval_status", ""))
    if approval_status != "APPROVED" and not allow_unapproved:
        raise PermissionError(f"model is not approved for formal execution: {model_id}")
    spec = ExecutableModelSpec(
        model_id=str(match["model_id"]),
        provider=str(match["provider"]),
        endpoint_or_checkpoint=str(match["endpoint_or_checkpoint"]),
        prompt_id=str(match["prompt_id"]),
        max_input_tokens=int(match["max_input_tokens"]),
        max_output_tokens=int(match["max_tokens"]),
        temperature=float(match["temperature"]),
        top_p=float(match.get("top_p", 1.0)),
        max_retries=int(match["retry"]),
        timeout_s=float(match["timeout_s"]),
        budget_usd=float(match["budget_usd"]),
        input_usd_per_1k_tokens=float(match["input_usd_per_1k_tokens"]),
        output_usd_per_1k_tokens=float(match["output_usd_per_1k_tokens"]),
        adapter_kind=str(match["adapter_kind"]),
        credential_env=str(match["credential_env"]),
        approval_status=approval_status,
    )
    spec.llm_config().validate()
    if spec.prompt_id not in PROMPT_REGISTRY:
        raise ValueError(f"unknown prompt_id in model matrix: {spec.prompt_id}")
    return spec


def _select_adapter(spec: ExecutableModelSpec) -> Adapter:
    if spec.adapter_kind == "openai_compatible_json":
        return openai_compatible_adapter
    raise NotImplementedError(f"unsupported adapter_kind for executable runner: {spec.adapter_kind}")


def _status_map_from_runs(runs: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    status_map: dict[str, str] = {}
    for run in runs:
        statuses = run.get("statuses", [])
        if isinstance(statuses, list) and statuses and all(item == "ok" for item in statuses):
            status_map[str(run.get("sample_id"))] = "ok"
        elif isinstance(statuses, list) and statuses:
            status_map[str(run.get("sample_id"))] = str(statuses[-1])
        else:
            status_map[str(run.get("sample_id"))] = "missing_prediction"
    return status_map


def run_formal_probe(
    samples: Sequence[Mapping[str, Any]],
    *,
    spec: ExecutableModelSpec,
    adapter: Adapter | None = None,
) -> dict[str, Any]:
    if any(sample.get("split") not in PROBE_ALLOWED_SPLITS for sample in samples):
        raise ValueError("formal probe only permits train_id or dev_id samples")
    llm_config = spec.llm_config()
    selected_adapter = adapter or _select_adapter(spec)

    def bound_adapter(sample: Mapping[str, Any], prompt: str, config: Mapping[str, Any]) -> Any:
        merged = dict(config)
        merged.update(
            {
                "endpoint_or_checkpoint": spec.endpoint_or_checkpoint,
                "credential_env": spec.credential_env,
            }
        )
        return selected_adapter(sample, prompt, merged)

    result = run_llm_pilot(
        samples,
        llm_config,
        adapter=bound_adapter,
    )
    prediction_map = {str(item["sample_id"]): item for item in result["predictions"]}
    statuses = _status_map_from_runs(result["dev_runs"])
    schema_errors = {
        sample_id: validate_prediction(prediction, dict(next(sample for sample in samples if sample.get("sample_id") == sample_id)))
        for sample_id, prediction in prediction_map.items()
    }
    score = score_samples(samples, prediction_map, statuses)
    probe_failed = bool(result["failures"]) or any(schema_errors.values()) or bool(score["failure_counts"])
    return {
        "runner_version": FORMAL_RUNNER_VERSION,
        "mode": "probe",
        "status": "PROBE_FAILED" if probe_failed else "PROBE_PASSED",
        "model_id": spec.model_id,
        "sample_count": len(samples),
        "executed_count": result["executed_count"],
        "config_sha256": result["config_sha256"],
        "cost": result["cost"],
        "failures": result["failures"],
        "schema_errors": schema_errors,
        "status_by_sample": statuses,
        "task_metrics": score["task_metrics"],
        "failure_counts": score["failure_counts"],
        "physical_violation_count": score["physical_violation_count"],
        "predictions": result["predictions"],
        "provider_usage": result["provider_usage"],
    }


def write_formal_probe(
    samples_path: Path,
    model_matrix_path: Path,
    output_path: Path,
    model_id: str,
    *,
    start_index: int = 0,
    max_samples: int | None = None,
    allow_unapproved: bool = False,
    adapter: Adapter | None = None,
) -> dict[str, Any]:
    samples = _load_samples(samples_path)
    if start_index < 0:
        raise ValueError("start_index must be non-negative")
    subset = samples[start_index:] if max_samples is None else samples[start_index:start_index + max_samples]
    spec = resolve_model_spec(model_matrix_path, model_id, allow_unapproved=allow_unapproved)
    result = run_formal_probe(subset, spec=spec, adapter=adapter)
    if output_path.exists():
        raise FileExistsError(f"probe output already exists: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def write_formal_run(
    samples_path: Path,
    model_matrix_path: Path,
    readiness_path: Path,
    output_root: Path,
    model_id: str,
    *,
    repository_root: Path,
    require_clean_git: bool = True,
    start_index: int = 0,
    max_samples: int | None = None,
    adapter: Adapter | None = None,
) -> dict[str, Any]:
    readiness = _load_mapping(readiness_path, "formal readiness")
    if readiness.get("status") != READY_STATUS:
        raise PermissionError("formal runner requires READY_FOR_FORMAL_MULTI_MODEL_FULL_RUN readiness")
    spec = resolve_model_spec(model_matrix_path, model_id)
    samples = _load_samples(samples_path)
    if start_index < 0:
        raise ValueError("start_index must be non-negative")
    subset = samples[start_index:] if max_samples is None else samples[start_index:start_index + max_samples]
    if any(sample.get("split") not in FORMAL_ALLOWED_SPLITS for sample in subset):
        raise ValueError("formal main runner only permits known formal split names")
    if output_root.exists():
        raise FileExistsError(f"formal run output already exists: {output_root}")
    git_commit = _ensure_clean_git(repository_root) if require_clean_git else "UNVERIFIED_GIT_FOR_TEST"
    llm_config = spec.llm_config()
    prompt_entry = PROMPT_REGISTRY[spec.prompt_id]
    prompt_hash = _hash(prompt_entry)
    public_root = output_root / "public"
    private_root = output_root / "private"
    public_root.mkdir(parents=True)
    private_root.mkdir(parents=True)
    selected_adapter = adapter or _select_adapter(spec)
    predictions: list[dict[str, Any]] = []
    run_index: list[dict[str, Any]] = []
    raw_lines: list[str] = []
    failures: list[dict[str, Any]] = []
    provider_usage: list[dict[str, Any]] = []
    spent_upper_bound = 0.0
    spent_actual = 0.0
    executed_count = 0
    for sample in subset:
        prompt = _render_prompt(sample, str(prompt_entry["prompt_template"]))
        estimated_input_tokens = min(llm_config.max_input_tokens, max(1, math.ceil(len(prompt) / 4)))
        worst_case_cost = (
            estimated_input_tokens * llm_config.input_usd_per_1k_tokens
            + llm_config.max_output_tokens * llm_config.output_usd_per_1k_tokens
        ) / 1000
        if spent_upper_bound + worst_case_cost > llm_config.max_cost_usd:
            failures.append(
                {
                    "sample_id": sample.get("sample_id"),
                    "status": "budget_blocked",
                    "estimated_incremental_usd": worst_case_cost,
                    "spent_upper_bound_usd": spent_upper_bound,
                    "budget_usd": llm_config.max_cost_usd,
                }
            )
            break
        started = time.perf_counter()
        raw = selected_adapter(
            sample,
            prompt,
            {
                "model_id": spec.model_id,
                "temperature": spec.temperature,
                "top_p": spec.top_p,
                "max_output_tokens": spec.max_output_tokens,
                "timeout_s": spec.timeout_s,
                "endpoint_or_checkpoint": spec.endpoint_or_checkpoint,
                "credential_env": spec.credential_env,
            },
        )
        latency_ms = round((time.perf_counter() - started) * 1000, 3)
        parsed = _parse_response(raw)
        if parsed is None:
            raise ValueError("formal adapter response is not a JSON object")
        raw_provider_response = parsed.pop("_raw_provider_response", raw)
        usage = parsed.pop("_provider_usage", {})
        prediction = _normalise_prediction(sample, parsed)
        validation_errors = validate_prediction(prediction, dict(sample))
        status = "ok" if not validation_errors else "invalid_prediction"
        input_tokens = usage.get("prompt_tokens", estimated_input_tokens)
        output_tokens = usage.get("completion_tokens", 0)
        actual_cost = (
            float(input_tokens) * llm_config.input_usd_per_1k_tokens
            + float(output_tokens) * llm_config.output_usd_per_1k_tokens
        ) / 1000
        spent_upper_bound += worst_case_cost
        spent_actual += actual_cost
        raw_sha = _hash(raw_provider_response)
        raw_lines.append(
            json.dumps(
                {
                    "sample_id": sample.get("sample_id"),
                    "model_id": spec.model_id,
                    "status": status,
                    "latency_ms": latency_ms,
                    "provider_usage": usage,
                    "validation_errors": validation_errors,
                    "raw_response": raw_provider_response,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        provider_usage.append({"sample_id": sample.get("sample_id"), "latency_ms": latency_ms, **dict(usage)})
        if validation_errors:
            failures.append({"sample_id": sample.get("sample_id"), "status": status, "validation_errors": validation_errors})
        predictions.append(prediction)
        run_index.append(
            {
                "run_id": output_root.name,
                "git_commit": git_commit,
                "input_manifest_hash": readiness.get("frozen_input_manifest_hash"),
                "model_matrix_hash": readiness.get("model_matrix_hash"),
                "calibration_hash": readiness.get("calibration_hash"),
                "preregistration_hash": readiness.get("preregistration_hash"),
                "runtime_hash": readiness.get("runtime_hash"),
                "prompt_hashes": [prompt_hash],
                "model_id": spec.model_id,
                "sample_id": sample.get("sample_id"),
                "repetition": 0,
                "status": status,
                "raw_response_sha256": raw_sha,
            }
        )
        executed_count += 1
    (private_root / "raw_responses.jsonl").write_text("\n".join(raw_lines) + ("\n" if raw_lines else ""), encoding="utf-8")
    public_predictions = {"predictions": predictions}
    (public_root / "predictions.json").write_text(json.dumps(public_predictions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    cost_latency_failures = {
        "runner_version": FORMAL_RUNNER_VERSION,
        "model_id": spec.model_id,
        "executed_count": executed_count,
        "spent_actual_usd": spent_actual,
        "spent_upper_bound_usd": spent_upper_bound,
        "budget_usd": llm_config.max_cost_usd,
        "provider_usage": provider_usage,
        "failures": failures,
    }
    (public_root / "cost_latency_failures.json").write_text(json.dumps(cost_latency_failures, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    run_manifest = {
        "runner_version": FORMAL_RUNNER_VERSION,
        "status": "COMPLETED_WITH_FAILURES" if failures else "COMPLETED",
        "run_id": output_root.name,
        "git_commit": git_commit,
        "model_id": spec.model_id,
        "sample_count": len(subset),
        "executed_count": executed_count,
        "private_raw_response": True,
        "predictions_path": "public/predictions.json",
        "cost_latency_failures_path": "public/cost_latency_failures.json",
        "run_index_path": "public/run_index.json",
        "test_asset_read": False,
        "runner_reads_gold": False,
    }
    (public_root / "run_manifest.json").write_text(json.dumps(run_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (public_root / "run_index.json").write_text(json.dumps(run_index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    private_manifest = {
        "runner_version": FORMAL_RUNNER_VERSION,
        "run_id": output_root.name,
        "public_manifest_hash": _hash(run_manifest),
        "predictions_hash": _hash(public_predictions),
        "cost_latency_failures_hash": _hash(cost_latency_failures),
        "raw_response_count": len(raw_lines),
        "test_gold_read": False,
    }
    (private_root / "private_manifest.json").write_text(json.dumps(private_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return run_manifest
