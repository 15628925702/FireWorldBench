"""Frozen LLM baseline contracts and train/dev-only pilot reporting."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

LLM_VERSION = "P4-BASELINE-LLM"
ALLOWED_SPLITS = {"train_id", "dev_id"}
TRACKS = {"text_only_table", "multimodal"}
Adapter = Callable[[Mapping[str, Any], str, Mapping[str, Any]], Any]

PROMPT_REGISTRY: dict[str, dict[str, Any]] = {
    "text_table_v1": {
        "track": "text_only_table",
        "prompt_template": "Task={task}; Sample={sample_id}; Answer only from supplied text/table observations.",
        "few_shot_ids": [],
        "input_budget_policy": "count_all_rendered_input_chars",
    },
    "multimodal_v1": {
        "track": "multimodal",
        "prompt_template": "Task={task}; Sample={sample_id}; Use only supplied approved visual and text observations.",
        "few_shot_ids": [],
        "input_budget_policy": "count_all_rendered_input_chars_and_visual_refs",
    },
}

MODEL_REGISTRY: dict[str, dict[str, Any]] = {
    "text_only_table": {
        "model_id": None,
        "status": "BLOCKED_UNTIL_MODEL_APPROVAL",
        "reason": "no_approved_model_id_or_api_budget",
    },
    "multimodal": {
        "model_id": None,
        "status": "BLOCKED_UNTIL_MODEL_APPROVAL",
        "reason": "no_approved_multimodal_model_or_visual_budget",
    },
}


@dataclass(frozen=True)
class LLMConfig:
    track: str
    prompt_id: str
    model_id: str | None = None
    approved: bool = False
    repeats: int = 1
    temperature: float = 0.0
    top_p: float = 1.0
    max_input_tokens: int = 4096
    max_output_tokens: int = 512
    max_retries: int = 0
    timeout_s: float = 30.0
    max_cost_usd: float = 0.0
    input_usd_per_1k_tokens: float = 0.0
    output_usd_per_1k_tokens: float = 0.0

    def validate(self) -> None:
        if self.track not in TRACKS:
            raise ValueError(f"unknown LLM track: {self.track}")
        prompt = PROMPT_REGISTRY.get(self.prompt_id)
        if prompt is None or prompt["track"] != self.track:
            raise ValueError("prompt_id does not match track")
        if self.repeats < 1 or self.max_retries < 0:
            raise ValueError("repeats must be positive and max_retries must be non-negative")
        if not 0.0 <= self.temperature <= 2.0 or not 0.0 < self.top_p <= 1.0:
            raise ValueError("sampling values are outside the frozen range")
        if self.max_input_tokens <= 0 or self.max_output_tokens <= 0:
            raise ValueError("token budgets must be positive")
        if self.timeout_s <= 0 or min(self.max_cost_usd, self.input_usd_per_1k_tokens, self.output_usd_per_1k_tokens) < 0:
            raise ValueError("timeout and cost budgets must be non-negative")
        if self.approved and not self.model_id:
            raise ValueError("approved configuration requires a complete model_id")


def _hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def freeze_config(config: LLMConfig) -> dict[str, Any]:
    config.validate()
    payload = asdict(config)
    payload["prompt"] = PROMPT_REGISTRY[config.prompt_id]
    payload["model_registry_entry"] = MODEL_REGISTRY[config.track]
    return {"config": payload, "config_sha256": _hash(payload), "frozen": True}


def _blocked_report(config: LLMConfig, sample_count: int) -> dict[str, Any]:
    frozen = freeze_config(config)
    return {
        "baseline_version": LLM_VERSION,
        "status": "BLOCKED",
        "block_reason": MODEL_REGISTRY[config.track]["reason"] if not config.approved else "adapter_not_configured",
        "track": config.track,
        "config_sha256": frozen["config_sha256"],
        "sample_count": sample_count,
        "executed_count": 0,
        "dev_runs": [],
        "variance": None,
        "cost": {"status": "N/A", "estimated_usd": None, "input_tokens": 0, "output_tokens": 0},
        "failures": [{"code": "MODEL_NOT_APPROVED", "count": sample_count}],
        "test_tuning": False,
        "test_asset_read": False,
    }


def _parse_response(raw: Any) -> dict[str, Any] | None:
    if isinstance(raw, Mapping):
        return dict(raw)
    if isinstance(raw, str):
        parsed = json.loads(raw)
        return dict(parsed) if isinstance(parsed, Mapping) else None
    return None


def run_llm_pilot(
    samples: Sequence[Mapping[str, Any]],
    config: LLMConfig,
    *,
    adapter: Adapter | None = None,
) -> dict[str, Any]:
    """Run a frozen adapter only on explicit train/dev samples."""

    config.validate()
    if any(sample.get("split") not in ALLOWED_SPLITS for sample in samples):
        raise ValueError("LLM pilot only permits train_id or dev_id")
    if not config.approved or adapter is None:
        return _blocked_report(config, len(samples))

    prompt_template = str(PROMPT_REGISTRY[config.prompt_id]["prompt_template"])
    runs: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    total_input_tokens = 0
    total_output_tokens = 0
    for sample in sorted(samples, key=lambda item: str(item.get("sample_id", ""))):
        prompt = prompt_template.format(task=sample.get("task", ""), sample_id=sample.get("sample_id", ""))
        input_tokens = min(config.max_input_tokens, max(1, math.ceil(len(prompt) / 4)))
        total_input_tokens += input_tokens * config.repeats
        labels: list[str] = []
        statuses: list[str] = []
        for repeat in range(config.repeats):
            status = "tool_error"
            parsed: dict[str, Any] | None = None
            error = ""
            for attempt in range(config.max_retries + 1):
                try:
                    raw = adapter(sample, prompt, asdict(config))
                    parsed = _parse_response(raw)
                    if parsed is None:
                        raise ValueError("adapter response is not a JSON object")
                    status = "ok"
                    break
                except Exception as exc:  # adapter boundary retains all failures
                    status = "failure"
                    error = f"{type(exc).__name__}: {exc}"
                    if attempt == config.max_retries:
                        failures.append({"sample_id": sample.get("sample_id"), "repeat": repeat, "error": error})
            if parsed is not None:
                label = parsed.get("answer", {}).get("label")
                if isinstance(label, str):
                    labels.append(label)
                total_output_tokens += min(config.max_output_tokens, max(1, math.ceil(len(json.dumps(parsed)) / 4)))
            statuses.append(status)
        runs.append({
            "sample_id": sample.get("sample_id"),
            "task": sample.get("task"),
            "split": sample.get("split"),
            "prompt_id": config.prompt_id,
            "repeats": config.repeats,
            "statuses": statuses,
            "label_distribution": dict(Counter(labels)),
        })

    estimated_cost = (total_input_tokens * config.input_usd_per_1k_tokens + total_output_tokens * config.output_usd_per_1k_tokens) / 1000
    if estimated_cost > config.max_cost_usd:
        failures.append({"code": "BUDGET_EXCEEDED", "estimated_usd": estimated_cost, "max_cost_usd": config.max_cost_usd})
    disagreement = sum(1 for run in runs if len(run["label_distribution"]) > 1)
    return {
        "baseline_version": LLM_VERSION,
        "status": "COMPLETED_WITH_FAILURES" if failures else "COMPLETED",
        "track": config.track,
        "model_id": config.model_id,
        "config_sha256": freeze_config(config)["config_sha256"],
        "sample_count": len(samples),
        "executed_count": len(runs),
        "dev_runs": runs,
        "variance": {"repeat_disagreement_rate": disagreement / len(runs) if runs else 0.0},
        "cost": {"status": "ESTIMATED", "estimated_usd": estimated_cost, "input_tokens": total_input_tokens, "output_tokens": total_output_tokens},
        "failures": failures,
        "test_tuning": False,
        "test_asset_read": False,
    }


def run_llm_pilot_file(
    samples_path: Path | None,
    config_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    config_payload = json.loads(config_path.read_text(encoding="utf-8"))
    config = LLMConfig(**config_payload["default_config"])
    samples: list[Mapping[str, Any]] = []
    if samples_path is not None:
        payload = json.loads(samples_path.read_text(encoding="utf-8"))
        value = payload.get("samples", payload) if isinstance(payload, Mapping) else payload
        if not isinstance(value, list):
            raise TypeError("LLM samples must be a JSON list or an object with a samples list")
        samples = value
    result = run_llm_pilot(samples, config)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
