"""OpenAI-compatible DeepSeek adapter for a small local planning pilot."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fireworldbench.llm_baseline import LLMConfig, run_llm_pilot

DEEPSEEK_ENDPOINT = "https://api.deepseek.com/chat/completions"


def deepseek_adapter(sample: Mapping[str, Any], prompt: str, config: Mapping[str, Any]) -> dict[str, Any]:
    """Call DeepSeek without persisting the API key or raw authorization details."""
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is required for the DeepSeek planning pilot")
    payload = {
        "model": str(config["model_id"]),
        "temperature": config["temperature"],
        "top_p": config["top_p"],
        "max_tokens": config["max_output_tokens"],
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": "Return only a valid JSON prediction. Never include hidden labels, gold, or scoring metadata.",
            },
            {"role": "user", "content": prompt},
        ],
    }
    endpoint = os.environ.get("DEEPSEEK_API_ENDPOINT", DEEPSEEK_ENDPOINT)
    request = Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=float(config["timeout_s"])) as response:  # nosec B310 - explicit approved endpoint
            raw = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"DeepSeek HTTP error {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError(f"DeepSeek network error: {exc.reason}") from exc
    choices = raw.get("choices", [])
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("DeepSeek response has no choices")
    content = choices[0].get("message", {}).get("content")
    if not isinstance(content, str):
        raise RuntimeError("DeepSeek response has no JSON content")
    prediction = json.loads(content)
    if not isinstance(prediction, dict):
        raise RuntimeError("DeepSeek JSON content is not an object")
    usage = raw.get("usage", {})
    prediction["_provider_usage"] = {
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
    }
    return prediction


def run_deepseek_pilot_file(
    samples_path: Path,
    config_path: Path,
    output_path: Path,
    *,
    start_index: int = 0,
    max_samples: int | None = None,
) -> dict[str, Any]:
    config_payload = json.loads(config_path.read_text(encoding="utf-8-sig"))
    if not isinstance(config_payload, Mapping):
        raise TypeError("DeepSeek pilot config must be an object")
    config = LLMConfig(**config_payload["default_config"])
    samples_payload = json.loads(samples_path.read_text(encoding="utf-8-sig"))
    samples = samples_payload.get("samples", samples_payload) if isinstance(samples_payload, Mapping) else samples_payload
    if not isinstance(samples, list):
        raise TypeError("DeepSeek pilot samples must be a JSON list or object with samples")
    configured_max = int(config_payload.get("max_samples", len(samples)))
    limit = configured_max if max_samples is None else min(configured_max, max_samples)
    if start_index < 0 or limit < 1:
        raise ValueError("max_samples must be positive")
    result = run_llm_pilot(samples[start_index:start_index + limit], config, adapter=deepseek_adapter)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
