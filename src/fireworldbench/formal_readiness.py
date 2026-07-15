"""Evidence-based readiness checks for the formal multi-model full run."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
import tomllib
from pathlib import Path
from typing import Any, Mapping, Sequence

FORMAL_READINESS_VERSION = "P5-MAIN-001-FORMAL-PREFLIGHT-v1"
READY_STATUS = "READY_FOR_FORMAL_MULTI_MODEL_FULL_RUN"
BLOCKED_STATUS = "BLOCKED_FORMAL_PREFLIGHT"
HEX = frozenset("0123456789abcdef")
MODEL_REQUIRED_FIELDS = {
    "model_id",
    "provider",
    "exact_model_version",
    "endpoint_or_checkpoint",
    "runtime",
    "tokenizer_version",
    "temperature",
    "max_tokens",
    "retry",
    "timeout_s",
    "concurrency",
    "pricing",
    "budget_usd",
    "prompt_hash",
    "parser_version",
    "failure_policy",
    "tasks",
    "tracks",
    "approval_status",
}
REQUIRED_TASKS = {"T1-A", "T1-B", "T1-C", "T2-A", "T2-B", "T2-C", "T3-A", "T3-B", "T3-C"}
PREREG_REQUIRED_FIELDS = {
    "hypotheses",
    "primary_metrics",
    "secondary_metrics",
    "model_track_matrix",
    "repetitions",
    "seeds",
    "aggregation_rules",
    "exclusions",
    "stopping_rules",
    "cost_ceiling_usd",
    "failure_rules",
    "robustness_plan",
    "ablation_plan",
    "test_embargo",
    "run_directory_rule",
    "raw_response_manifest",
    "cost_latency_failure_manifest",
    "paper_number_provenance",
}


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and set(value.casefold()) <= HEX


def _load_mapping(path: Path, label: str) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be a JSON object")
    return dict(value)


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def _relative_files(root: Path) -> list[dict[str, Any]]:
    if not root.is_dir():
        return []
    files: list[dict[str, Any]] = []
    for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: item.as_posix().casefold()):
        files.append(
            {
                "relative_path": path.relative_to(root).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": _file_sha256(path),
            }
        )
    return files


def build_formal_input_audit(
    data_sources_path: Path,
    staging_assessment_path: Path,
    d01_tree_path: Path,
    *,
    repository_root: Path,
) -> dict[str, Any]:
    """Inventory permitted staging roots without treating them as formal inputs."""

    with data_sources_path.open("rb") as handle:
        source_config = tomllib.load(handle)
    assessment = _load_mapping(staging_assessment_path, "staging assessment")
    tree = _load_mapping(d01_tree_path, "D01 upstream tree")
    assessment_by_id = {
        str(item.get("dataset_id")): item
        for item in assessment.get("datasets", [])
        if isinstance(item, Mapping) and item.get("dataset_id")
    }
    datasets: list[dict[str, Any]] = []
    blockers: list[str] = []
    for raw_source in source_config.get("sources", []):
        if not isinstance(raw_source, Mapping):
            continue
        dataset_id = str(raw_source.get("id", ""))
        staging_value = raw_source.get("staging_dir")
        staging_root = repository_root / str(staging_value) if staging_value else None
        files = _relative_files(staging_root) if staging_root is not None else []
        stage = assessment_by_id.get(dataset_id, {})
        planning_manifest_value = raw_source.get("planning_manifest")
        planning_manifest_path = (
            repository_root / str(planning_manifest_value) if planning_manifest_value else None
        )
        planning_manifest = (
            _load_mapping(planning_manifest_path, f"{dataset_id} planning manifest")
            if planning_manifest_path is not None and planning_manifest_path.is_file()
            else {}
        )
        eligible = raw_source.get("eligible") is True
        dataset_blockers: list[str] = []
        if not eligible:
            dataset_blockers.append("formal_benchmark_eligible_false")
        if not files:
            dataset_blockers.append("no_staged_files")
        license_status = str(raw_source.get("license_status", "missing"))
        version_status = str(raw_source.get("version_status", "missing"))
        if license_status.startswith("blocked"):
            dataset_blockers.append("license_evidence_blocked")
        if version_status.startswith("blocked"):
            dataset_blockers.append("source_version_evidence_blocked")
        entry: dict[str, Any] = {
            "dataset_id": dataset_id,
            "name": raw_source.get("name"),
            "source_url": raw_source.get("source_url"),
            "acquisition_date": planning_manifest.get("acquisition_date"),
            "source_version": planning_manifest.get("upstream_version_or_commit"),
            "registered_local_dirs": raw_source.get("local_dirs", []),
            "planning_download_status": raw_source.get("planning_download_status"),
            "roles": raw_source.get("roles", []),
            "planning_manifest": planning_manifest_value,
            "planning_manifest_sha256": _file_sha256(planning_manifest_path)
            if planning_manifest_path is not None and planning_manifest_path.is_file()
            else None,
            "staging_root": staging_value,
            "file_count": len(files),
            "total_bytes": sum(int(item["size_bytes"]) for item in files),
            "files": files,
            "inventory_sha256": _canonical_sha256(files),
            "canonical_status": stage.get("status", "NOT_ASSESSED"),
            "canonical_record_count": stage.get("canonical_probe", {}).get("record_count", 0)
            if isinstance(stage.get("canonical_probe"), Mapping)
            else 0,
            "canonical_case_count": stage.get("canonical_probe", {}).get("case_count", 0)
            if isinstance(stage.get("canonical_probe"), Mapping)
            else 0,
            "formal_benchmark_eligible": eligible,
            "license_status": license_status,
            "version_status": version_status,
            "blockers": sorted(set(dataset_blockers)),
        }
        datasets.append(entry)
        blockers.extend(f"{dataset_id}:{item}" for item in dataset_blockers)

    d01 = next((item for item in datasets if item["dataset_id"] == "D01"), None)
    official = [
        item
        for item in tree.get("tree", [])
        if isinstance(item, Mapping) and str(item.get("path", "")).startswith("CFD-Data/") and str(item.get("path", "")).casefold().endswith(".csv")
    ]
    if d01 is not None:
        local_by_name = {Path(str(item["relative_path"])).name: item for item in d01["files"]}
        missing = [
            {
                "relative_path": str(item["path"]),
                "size_bytes": int(item.get("size", 0)),
                "upstream_git_blob_sha": item.get("sha"),
                "sha256": None,
            }
            for item in official
            if Path(str(item["path"])).name not in local_by_name
        ]
        local_csv_count = sum(1 for item in d01["files"] if str(item["relative_path"]).casefold().endswith(".csv"))
        d01["official_inventory"] = {
            "declared_csv_count": len(official),
            "declared_bytes": sum(int(item.get("size", 0)) for item in official),
            "local_csv_count": local_csv_count,
            "missing_csv_count": len(missing),
            "missing_files": missing,
            "tree_source": d01_tree_path.as_posix(),
        }
        if missing:
            d01["blockers"].append("official_files_missing")
            blockers.append(f"D01:official_files_missing:{len(missing)}")

    formal_files = [
        {"dataset_id": dataset["dataset_id"], **file}
        for dataset in datasets
        if dataset["formal_benchmark_eligible"] and not dataset["blockers"]
        for file in dataset["files"]
    ]
    if not formal_files:
        blockers.append("paper_ready_formal_input_files_missing")
    blockers.extend(
        [
            "group_first_split_audit_missing",
            "leak_audit_missing_for_formal_inputs",
            "case_scenario_family_sequence_uniqueness_missing",
        ]
    )
    result: dict[str, Any] = {
        "schema_version": 1,
        "manifest_id": "P5-MAIN-001-FORMAL-INPUT-AUDIT",
        "status": "FROZEN_FORMAL_INPUTS" if not blockers else "BLOCKED_NO_PAPER_READY_FORMAL_INPUTS",
        "datasets": datasets,
        "formal_input_files": formal_files,
        "formal_input_file_count": len(formal_files),
        "split_audit": "PASS" if not blockers else "BLOCKED_NO_FORMAL_CASE_MANIFEST",
        "leak_audit": "PASS" if not blockers else "BLOCKED_NO_FORMAL_CASE_MANIFEST",
        "uniqueness_audit": "PASS" if not blockers else "BLOCKED_NO_FORMAL_CASE_MANIFEST",
        "staging_assessment_sha256": _file_sha256(staging_assessment_path),
        "raw_files_modified": False,
        "test_private_assets_accessed": False,
        "planning_inputs_promoted_to_formal": False,
        "blockers": sorted(set(blockers)),
    }
    result["canonical_manifest_sha256"] = _canonical_sha256(result)
    return result


def write_formal_input_audit(
    output_path: Path,
    data_sources_path: Path,
    staging_assessment_path: Path,
    d01_tree_path: Path,
    *,
    repository_root: Path,
) -> dict[str, Any]:
    result = build_formal_input_audit(
        data_sources_path,
        staging_assessment_path,
        d01_tree_path,
        repository_root=repository_root,
    )
    _write_json(output_path, result)
    return result


def _validate_data(data: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    declared_hash = data.get("canonical_manifest_sha256")
    unhashed = dict(data)
    unhashed.pop("canonical_manifest_sha256", None)
    if declared_hash != _canonical_sha256(unhashed):
        blockers.append("data:canonical_manifest_hash_mismatch")
    if data.get("status") != "FROZEN_FORMAL_INPUTS":
        blockers.append("data:not_frozen_for_formal_run")
    files = data.get("formal_input_files")
    if not isinstance(files, list) or not files:
        blockers.append("data:formal_input_files_missing")
    elif any(not isinstance(item, Mapping) or not item.get("relative_path") or not _is_sha256(item.get("sha256")) for item in files):
        blockers.append("data:input_file_identity_incomplete")
    for field in ("split_audit", "leak_audit", "uniqueness_audit"):
        if data.get(field) != "PASS":
            blockers.append(f"data:{field}_not_passed")
    if data.get("test_private_assets_accessed") is not False:
        blockers.append("data:test_private_access_not_clean")
    return blockers


def _validate_models(matrix: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    if matrix.get("status") != "APPROVED_FROZEN":
        blockers.append("models:matrix_not_approved_frozen")
    models = matrix.get("models")
    if not isinstance(models, list) or len(models) < 2:
        blockers.append("models:at_least_two_models_required")
        return blockers
    for index, raw_model in enumerate(models):
        label = f"models:{index}"
        if not isinstance(raw_model, Mapping):
            blockers.append(f"{label}:not_an_object")
            continue
        missing = sorted(MODEL_REQUIRED_FIELDS - raw_model.keys())
        if missing:
            blockers.append(f"{label}:missing_fields:{','.join(missing)}")
        if raw_model.get("approval_status") != "APPROVED":
            blockers.append(f"{label}:not_approved")
        if any(raw_model.get(field) in (None, "", []) for field in MODEL_REQUIRED_FIELDS - {"tasks", "tracks"}):
            blockers.append(f"{label}:required_value_missing")
        if not _is_sha256(raw_model.get("prompt_hash")):
            blockers.append(f"{label}:prompt_hash_invalid")
        tasks = set(raw_model.get("tasks", []))
        if not REQUIRED_TASKS <= tasks:
            blockers.append(f"{label}:task_coverage_incomplete")
    return blockers


def _validate_calibration(calibration: Mapping[str, Any], approved_model_ids: set[str]) -> list[str]:
    blockers: list[str] = []
    if calibration.get("status") != "FROZEN_COMPLETE":
        blockers.append("calibration:not_frozen_complete")
    if calibration.get("test_contaminated") is not False or calibration.get("test_asset_read") is not False:
        blockers.append("calibration:test_contamination_not_excluded")
    if not _is_sha256(calibration.get("config_sha256")):
        blockers.append("calibration:config_hash_missing")
    results = calibration.get("results")
    result_models = {
        str(item.get("model_id")) for item in results if isinstance(item, Mapping) and item.get("model_id")
    } if isinstance(results, list) else set()
    if not approved_model_ids or not approved_model_ids <= result_models:
        blockers.append("calibration:approved_model_results_incomplete")
    return blockers


def _validate_prereg(prereg: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    if prereg.get("status") != "FROZEN":
        blockers.append("preregistration:not_frozen")
    missing = sorted(PREREG_REQUIRED_FIELDS - prereg.keys())
    if missing:
        blockers.append(f"preregistration:missing_fields:{','.join(missing)}")
    metrics = prereg.get("primary_metrics")
    if not isinstance(metrics, Mapping) or set(metrics) != REQUIRED_TASKS:
        blockers.append("preregistration:primary_metrics_not_exactly_nine_tasks")
    embargo = prereg.get("test_embargo")
    if not isinstance(embargo, Mapping) or embargo.get("test_input_read") is not False or embargo.get("test_gold_read") is not False or embargo.get("private_mapping_read") is not False:
        blockers.append("preregistration:test_embargo_invalid")
    if prereg.get("cost_ceiling_usd") in (None, 0, 0.0):
        blockers.append("preregistration:cost_ceiling_not_approved")
    return blockers


def _validate_runtime(runtime: Mapping[str, Any], approved_model_ids: set[str]) -> list[str]:
    blockers: list[str] = []
    if runtime.get("status") != "APPROVED_FROZEN":
        blockers.append("runtime:not_approved_frozen")
    if not _is_sha256(runtime.get("environment_lock_sha256")):
        blockers.append("runtime:environment_lock_missing")
    model_runtimes = runtime.get("model_runtimes")
    available = {
        str(item.get("model_id"))
        for item in model_runtimes
        if isinstance(item, Mapping) and item.get("available") is True and item.get("model_id")
    } if isinstance(model_runtimes, list) else set()
    if not approved_model_ids or not approved_model_ids <= available:
        blockers.append("runtime:approved_model_runtime_incomplete")
    return blockers


def _validate_run_contract(run: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    if run.get("status") != "FROZEN":
        blockers.append("run_contract:not_frozen")
    for field in ("run_index_schema", "output_schema", "provenance_chain", "raw_response_manifest", "cost_latency_failure_manifest"):
        if not run.get(field):
            blockers.append(f"run_contract:{field}_missing")
    if run.get("formal_run_started") is not False or run.get("formal_results_written") is not False:
        blockers.append("run_contract:formal_run_already_started")
    return blockers


def assess_formal_readiness(
    data_path: Path,
    model_matrix_path: Path,
    calibration_path: Path,
    prereg_path: Path,
    runtime_path: Path,
    run_contract_path: Path,
) -> dict[str, Any]:
    inputs = {
        "data": data_path,
        "model_matrix": model_matrix_path,
        "calibration": calibration_path,
        "preregistration": prereg_path,
        "runtime": runtime_path,
        "run_contract": run_contract_path,
    }
    payloads = {name: _load_mapping(path, name) for name, path in inputs.items()}
    approved_model_ids = {
        str(item.get("model_id"))
        for item in payloads["model_matrix"].get("models", [])
        if isinstance(item, Mapping) and item.get("approval_status") == "APPROVED" and item.get("model_id")
    }
    blockers = [
        *_validate_data(payloads["data"]),
        *_validate_models(payloads["model_matrix"]),
        *_validate_calibration(payloads["calibration"], approved_model_ids),
        *_validate_prereg(payloads["preregistration"]),
        *_validate_runtime(payloads["runtime"], approved_model_ids),
        *_validate_run_contract(payloads["run_contract"]),
    ]
    artifact_chain = {
        name: {"path": path.as_posix(), "sha256": _file_sha256(path)} for name, path in inputs.items()
    }
    prompt_hashes = sorted(
        {
            str(item.get("prompt_hash"))
            for item in payloads["model_matrix"].get("models", [])
            if isinstance(item, Mapping) and _is_sha256(item.get("prompt_hash"))
        }
    )
    result: dict[str, Any] = {
        "readiness_version": FORMAL_READINESS_VERSION,
        "status": READY_STATUS if not blockers else BLOCKED_STATUS,
        "blockers": sorted(set(blockers)),
        "artifact_chain": artifact_chain,
        "frozen_input_manifest_hash": artifact_chain["data"]["sha256"],
        "model_matrix_hash": artifact_chain["model_matrix"]["sha256"],
        "calibration_hash": artifact_chain["calibration"]["sha256"],
        "preregistration_hash": artifact_chain["preregistration"]["sha256"],
        "runtime_hash": artifact_chain["runtime"]["sha256"],
        "run_contract_hash": artifact_chain["run_contract"]["sha256"],
        "prompt_hashes": prompt_hashes,
        "environment_observation": {
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "conda_default_env": os.environ.get("CONDA_DEFAULT_ENV"),
            "formal_environment_active": os.environ.get("CONDA_DEFAULT_ENV") == "fireworldbench-v1",
            "executable_name": Path(sys.executable).name,
        },
        "formal_run_started": False,
        "formal_model_results_generated": False,
        "paper_numbers_generated": False,
        "test_private_assets_accessed": False,
    }
    result["readiness_manifest_sha256"] = _canonical_sha256(result)
    return result


def write_formal_readiness(
    output_path: Path,
    data_path: Path,
    model_matrix_path: Path,
    calibration_path: Path,
    prereg_path: Path,
    runtime_path: Path,
    run_contract_path: Path,
) -> dict[str, Any]:
    result = assess_formal_readiness(
        data_path,
        model_matrix_path,
        calibration_path,
        prereg_path,
        runtime_path,
        run_contract_path,
    )
    _write_json(output_path, result)
    return result
