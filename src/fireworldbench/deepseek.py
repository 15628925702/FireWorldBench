"""OpenAI-compatible adapters used by DeepSeek and guarded formal probes."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fireworldbench.llm_baseline import LLMConfig, run_llm_pilot

DEEPSEEK_ENDPOINT = "https://api.deepseek.com/chat/completions"


def _call_openai_compatible_json(
    *,
    endpoint: str,
    api_key: str,
    model_id: str,
    prompt: str,
    temperature: float,
    top_p: float,
    max_output_tokens: int,
    timeout_s: float,
    system_prompt: str,
) -> dict[str, Any]:
    payload = {
        "model": model_id,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_output_tokens,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
    }
    request = Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_s) as response:  # nosec B310 - explicit approved endpoint
            raw = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"HTTP error {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError(f"network error: {exc.reason}") from exc
    if not isinstance(raw, Mapping):
        raise RuntimeError("provider response is not a JSON object")
    return dict(raw)


def openai_compatible_adapter(sample: Mapping[str, Any], prompt: str, config: Mapping[str, Any]) -> dict[str, Any]:
    """Call a frozen OpenAI-compatible JSON endpoint without persisting credentials."""

    credential_env = str(config.get("credential_env") or "")
    if not credential_env:
        raise RuntimeError("credential_env is required for the OpenAI-compatible adapter")
    api_key = os.environ.get(credential_env)
    if not api_key:
        raise RuntimeError(f"{credential_env} is required for the OpenAI-compatible adapter")
    endpoint = str(config.get("endpoint_or_checkpoint") or "").strip()
    if not endpoint:
        raise RuntimeError("endpoint_or_checkpoint is required for the OpenAI-compatible adapter")
    system_prompt = str(
        config.get(
            "system_prompt")
        or "Return only a valid JSON prediction. Never include hidden labels, gold, or scoring metadata."
    )
    raw = _call_openai_compatible_json(
        endpoint=endpoint,
        api_key=api_key,
        model_id=str(config["model_id"]),
        prompt=prompt,
        temperature=float(config.get("temperature", 0.0)),
        top_p=float(config.get("top_p", 1.0)),
        max_output_tokens=int(config.get("max_output_tokens", config.get("max_tokens", 240))),
        timeout_s=float(config.get("timeout_s", 60.0)),
        system_prompt=system_prompt,
    )
    choices = raw.get("choices", [])
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("provider response has no choices")
    content = choices[0].get("message", {}).get("content")
    if not isinstance(content, str):
        raise RuntimeError("provider response has no JSON content")
    prediction = json.loads(content)
    if not isinstance(prediction, dict):
        raise RuntimeError("provider JSON content is not an object")
    usage = raw.get("usage", {})
    prediction["_provider_usage"] = {
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
    }
    prediction["_raw_provider_response"] = raw
    return prediction


def deepseek_adapter(sample: Mapping[str, Any], prompt: str, config: Mapping[str, Any]) -> dict[str, Any]:
    """Call DeepSeek without persisting the API key or raw authorization details."""
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is required for the DeepSeek planning pilot")
    endpoint = os.environ.get("DEEPSEEK_API_ENDPOINT", DEEPSEEK_ENDPOINT)
    raw = _call_openai_compatible_json(
        endpoint=endpoint,
        api_key=api_key,
        model_id=str(config["model_id"]),
        prompt=prompt,
        temperature=float(config["temperature"]),
        top_p=float(config["top_p"]),
        max_output_tokens=int(config["max_output_tokens"]),
        timeout_s=float(config["timeout_s"]),
        system_prompt="Return only a valid JSON prediction. Never include hidden labels, gold, or scoring metadata.",
    )
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
    prediction["_raw_provider_response"] = raw
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
