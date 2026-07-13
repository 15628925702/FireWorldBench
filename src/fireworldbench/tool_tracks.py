"""Independent, replayable tool tracks for train/dev ablation contracts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

TOOL_VERSION = "P4-TOOL-001"
ALLOWED_SPLITS = {"train_id", "dev_id"}
TRACKS = {"retrieval", "plot", "formula_fds_proxy", "tool_use"}
ToolHandler = Callable[[Mapping[str, Any]], Any]
TrackAdapter = Callable[[Mapping[str, Any], "ToolSandbox", Mapping[str, Any]], Any]


def _hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class ToolPolicy:
    track: str
    knowledge_base_id: str
    allowed_tools: tuple[str, ...]
    max_calls: int
    max_cost_units: int
    information_budget: str

    def validate(self) -> None:
        if self.track not in TRACKS:
            raise ValueError(f"unknown tool track: {self.track}")
        if not self.knowledge_base_id:
            raise ValueError("knowledge_base_id must be frozen")
        if self.max_calls < 0 or self.max_cost_units < 0:
            raise ValueError("tool limits must be non-negative")
        if len(set(self.allowed_tools)) != len(self.allowed_tools):
            raise ValueError("allowed_tools must not contain duplicates")
        if not self.information_budget:
            raise ValueError("information_budget must be frozen")


DEFAULT_POLICIES: dict[str, ToolPolicy] = {
    "retrieval": ToolPolicy("retrieval", "KB_NOT_APPROVED", ("knowledge_base_lookup",), 2, 2, "retrieval_only"),
    "plot": ToolPolicy("plot", "NO_PLOT_DATASET_APPROVED", ("plot_series",), 2, 2, "plot_only"),
    "formula_fds_proxy": ToolPolicy("formula_fds_proxy", "FDS_PROXY_NOT_APPROVED", ("formula_eval", "fds_proxy"), 2, 4, "formula_or_fds_proxy_only"),
    "tool_use": ToolPolicy("tool_use", "KB_PLOT_FORMULA_REGISTRY_FROZEN", ("knowledge_base_lookup", "plot_series", "formula_eval", "fds_proxy"), 4, 8, "declared_tool_use_only"),
}


class ToolSandbox:
    """A single-track sandbox that records every accepted or rejected call."""

    def __init__(self, policy: ToolPolicy, handlers: Mapping[str, ToolHandler] | None = None) -> None:
        policy.validate()
        self.policy = policy
        self.handlers = dict(handlers or {})
        self.trace: list[dict[str, Any]] = []
        self.cost_units = 0

    def call(self, tool: str, args: Mapping[str, Any]) -> Any:
        sequence = len(self.trace) + 1
        status = "ok"
        result: Any = None
        error: str | None = None
        if tool not in self.policy.allowed_tools:
            status, error = "rejected_tool", "tool is not on the frozen whitelist"
        elif sequence > self.policy.max_calls:
            status, error = "rejected_call_limit", "maximum tool calls exceeded"
        elif tool not in self.handlers:
            status, error = "tool_unavailable", "no local handler is configured"
        else:
            try:
                result = self.handlers[tool](dict(args))
                next_cost = self.cost_units + 1
                if next_cost > self.policy.max_cost_units:
                    status, error = "rejected_cost_limit", "maximum cost units exceeded"
                    result = None
                else:
                    self.cost_units = next_cost
            except Exception as exc:  # tool boundary retains failures
                status, error = "tool_error", f"{type(exc).__name__}: {exc}"
        event = {
            "sequence": sequence,
            "track": self.policy.track,
            "tool": tool,
            "args": dict(args),
            "args_sha256": _hash(args),
            "status": status,
            "result": result,
            "result_sha256": _hash(result) if status == "ok" else None,
            "error": error,
            "cost_units": 1 if status == "ok" else 0,
        }
        self.trace.append(event)
        return result if status == "ok" else {"status": status, "error": error}


def replay_trace(trace: Sequence[Mapping[str, Any]]) -> list[Any]:
    """Replay recorded outputs without calling any external tool."""

    outputs: list[Any] = []
    for expected_sequence, event in enumerate(trace, start=1):
        if event.get("sequence") != expected_sequence:
            raise ValueError("trace sequence is not contiguous")
        if event.get("status") == "ok" and event.get("result_sha256") != _hash(event.get("result")):
            raise ValueError("trace result hash mismatch")
        outputs.append(event.get("result") if event.get("status") == "ok" else {"status": event.get("status"), "error": event.get("error")})
    return outputs


def freeze_tool_policies(policies: Mapping[str, ToolPolicy] = DEFAULT_POLICIES) -> dict[str, Any]:
    normalized = {name: asdict(policy) for name, policy in sorted(policies.items())}
    for policy in policies.values():
        policy.validate()
    return {"policies": normalized, "policies_sha256": _hash(normalized), "frozen": True}


def _blocked_report(samples: Sequence[Mapping[str, Any]], policies: Mapping[str, ToolPolicy]) -> dict[str, Any]:
    frozen = freeze_tool_policies(policies)
    return {
        "tool_version": TOOL_VERSION,
        "status": "BLOCKED",
        "block_reason": "no_approved_model_or_tool_runtime",
        "policies_sha256": frozen["policies_sha256"],
        "tracks": {name: {"status": "BLOCKED", "sample_count": len(samples), "runs": [], "trace": [], "failures": [{"code": "MODEL_NOT_APPROVED", "count": len(samples)}], "cost_units": 0} for name in sorted(policies)},
        "budget_mixing": False,
        "joint_ranking": False,
        "test_asset_read": False,
    }


def run_tool_ablation(
    samples: Sequence[Mapping[str, Any]],
    *,
    policies: Mapping[str, ToolPolicy] = DEFAULT_POLICIES,
    adapter: TrackAdapter | None = None,
) -> dict[str, Any]:
    """Run each information budget independently on explicit train/dev samples."""

    if any(sample.get("split") not in ALLOWED_SPLITS for sample in samples):
        raise ValueError("tool ablation only permits train_id or dev_id")
    for policy in policies.values():
        policy.validate()
    if adapter is None:
        return _blocked_report(samples, policies)

    track_reports: dict[str, Any] = {}
    for name, policy in sorted(policies.items()):
        sandbox = ToolSandbox(policy)
        runs: list[dict[str, Any]] = []
        failures: list[dict[str, Any]] = []
        for sample in sorted(samples, key=lambda item: str(item.get("sample_id", ""))):
            try:
                response = adapter(sample, sandbox, {"track": name, "information_budget": policy.information_budget})
                if not isinstance(response, Mapping):
                    raise ValueError("adapter response must be a mapping")
                runs.append({"sample_id": sample.get("sample_id"), "status": "ok", "answer": response.get("answer")})
            except Exception as exc:  # model boundary retains failures
                failures.append({"sample_id": sample.get("sample_id"), "error": f"{type(exc).__name__}: {exc}"})
        track_reports[name] = {
            "status": "COMPLETED_WITH_FAILURES" if failures else "COMPLETED",
            "information_budget": policy.information_budget,
            "sample_count": len(samples),
            "runs": runs,
            "trace": sandbox.trace,
            "trace_replay": replay_trace(sandbox.trace),
            "failures": failures,
            "cost_units": sandbox.cost_units,
        }
    return {
        "tool_version": TOOL_VERSION,
        "status": "COMPLETED",
        "policies_sha256": freeze_tool_policies(policies)["policies_sha256"],
        "tracks": track_reports,
        "budget_mixing": False,
        "joint_ranking": False,
        "test_asset_read": False,
    }


def run_tool_ablation_file(config_path: Path, output_path: Path, samples_path: Path | None = None) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    policies: dict[str, ToolPolicy] = {}
    for name, value in config["policies"].items():
        policies[name] = ToolPolicy(
            track=name,
            knowledge_base_id=str(value["knowledge_base_id"]),
            allowed_tools=tuple(value["allowed_tools"]),
            max_calls=int(value["max_calls"]),
            max_cost_units=int(value["max_cost_units"]),
            information_budget=str(value["information_budget"]),
        )
    samples: list[Mapping[str, Any]] = []
    if samples_path is not None:
        payload = json.loads(samples_path.read_text(encoding="utf-8"))
        value = payload.get("samples", payload) if isinstance(payload, Mapping) else payload
        if not isinstance(value, list):
            raise TypeError("tool samples must be a JSON list or an object with a samples list")
        samples = value
    result = run_tool_ablation(samples, policies=policies)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
