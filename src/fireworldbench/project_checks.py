"""Shared project bootstrap validation."""

from __future__ import annotations

import hashlib
import json
import re
import tomllib
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

CORE_PDF = Path("开发要求约束/FireWorldBench_Benchmark_Design_v2.pdf")
CORE_PDF_SHA256 = "16b4caec881825b8a8d41556a5abe6a428ae77944c98c45e56789add54c8d7ce"
PLACEHOLDER_IDS = {"D07", "D08", "D09", "D11"}

REQUIRED_PATHS = (
    Path("AGENTS.md"),
    Path("README.md"),
    Path("PROJECT_CHARTER.md"),
    Path("ROADMAP.md"),
    Path("environment.yml"),
    Path("开发要求约束/开发约束总则.md"),
    Path("开发要求约束/Definition_of_Done.md"),
    Path("开发要求约束/测试集封存与访问控制.md"),
    Path("进度跟进记录/CURRENT_STATUS.md"),
    Path("进度跟进记录/SESSION_HANDOFF_TEMPLATE.md"),
    Path("进度跟进记录/NEXT_SESSION_PROMPT.md"),
    Path("进度跟进记录/多窗口开发执行手册.md"),
    Path("进度跟进记录/窗口切换与中断恢复模板.md"),
    Path("进度跟进记录/任务指令库_从P0到论文数据导出.md"),
    Path("详细设计规划/00_总体架构与实现设计.md"),
    Path("详细设计规划/01_数据与样本协议.md"),
    Path("详细设计规划/02_任务与评测协议.md"),
    Path("详细设计规划/03_实验与论文规划.md"),
    Path("详细设计规划/04_里程碑与验收标准.md"),
    Path("详细设计规划/05_论文数据导出规范.md"),
    Path("项目治理/决策记录.md"),
    Path("项目治理/风险登记.md"),
    Path("项目治理/开放问题.md"),
    Path("项目治理/数据资产登记.md"),
    Path("项目治理/论文证据矩阵.md"),
    Path("项目治理/测试集访问记录.md"),
    Path("configs/project.toml"),
    Path("configs/data_sources.toml"),
    Path("configs/splits.toml"),
    Path("configs/evaluation.toml"),
    Path("configs/test_embargo.toml"),
    Path("schemas/benchmark_sample.schema.json"),
    Path("schemas/prediction.schema.json"),
    CORE_PDF,
)


def discover_project_root(start: Path | None = None) -> Path:
    """Find a source checkout; installed CLIs can use --root outside a checkout."""
    candidate = (start or Path.cwd()).resolve()
    if candidate.is_file():
        candidate = candidate.parent
    for directory in (candidate, *candidate.parents):
        if (directory / "pyproject.toml").is_file() and (directory / "configs").is_dir():
            return directory
    raise FileNotFoundError("FireWorldBench project root not found; pass `fwb doctor --root PATH`")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_toml(root: Path, relative: str) -> dict[str, Any]:
    with (root / relative).open("rb") as handle:
        return tomllib.load(handle)


def _load_json(root: Path, relative: str) -> dict[str, Any]:
    with (root / relative).open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise TypeError(f"{relative} must contain a JSON object")
    return value


def _load_front_matter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise ValueError(f"missing front matter in {path.name}")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError(f"unterminated front matter in {path.name}") from exc
    metadata: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip():
            continue
        key, separator, value = line.partition(":")
        if not separator or not key.strip() or not value.strip():
            raise ValueError(f"invalid front matter line in {path.name}: {line!r}")
        metadata[key.strip()] = value.strip()
    return metadata


def _iter_strings(value: object) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for item in value.values():
            yield from _iter_strings(item)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            yield from _iter_strings(item)


def is_absolute_path_like(value: str) -> bool:
    """Detect personal absolute paths while allowing URLs and ordinary identifiers."""
    if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://", value):
        return False
    if value.startswith(("~/", "~\\", "\\\\", "//")):
        return True
    return PureWindowsPath(value).is_absolute() or PurePosixPath(value).is_absolute()


def _require_equal(errors: list[str], actual: object, expected: object, label: str) -> None:
    if actual != expected:
        errors.append(f"{label} must be {expected!r}, got {actual!r}")


def validate_project(root: Path) -> list[str]:
    """Return all bootstrap invariant violations for a project checkout."""
    root = root.resolve()
    errors: list[str] = []

    for relative in REQUIRED_PATHS:
        path = root / relative
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"missing or empty required file: {relative}")

    if (root / CORE_PDF).is_file() and _sha256(root / CORE_PDF) != CORE_PDF_SHA256:
        errors.append("core design PDF SHA-256 changed without updating the project baseline")

    try:
        documents = {
            "project": _load_toml(root, "configs/project.toml"),
            "sources": _load_toml(root, "configs/data_sources.toml"),
            "splits": _load_toml(root, "configs/splits.toml"),
            "evaluation": _load_toml(root, "configs/evaluation.toml"),
            "embargo": _load_toml(root, "configs/test_embargo.toml"),
        }
        schemas = {
            "benchmark_sample": _load_json(root, "schemas/benchmark_sample.schema.json"),
            "prediction": _load_json(root, "schemas/prediction.schema.json"),
        }
    except (OSError, TypeError, json.JSONDecodeError, tomllib.TOMLDecodeError) as exc:
        errors.append(f"configuration/schema parse failure: {exc}")
        return errors

    for name, schema in schemas.items():
        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as exc:
            errors.append(f"invalid Draft 2020-12 schema {name}: {exc.message}")

    project_policy = documents["project"].get("policy", {})
    for key in (
        "raw_data_read_only",
        "split_before_windowing",
        "placeholder_data_must_be_ineligible",
        "test_labels_private",
        "frozen_runs_are_immutable",
    ):
        _require_equal(errors, project_policy.get(key), True, f"project.policy.{key}")

    split = documents["splits"].get("split", {})
    _require_equal(errors, split.get("strategy"), "group_first", "splits.split.strategy")
    _require_equal(
        errors,
        split.get("split_before_windowing"),
        True,
        "splits.split.split_before_windowing",
    )

    leakage = documents["splits"].get("leakage", {})
    for key in (
        "exact_hash",
        "perceptual_hash",
        "temporal_neighbor",
        "family_overlap",
        "template_overlap",
        "metadata_answer_cue",
    ):
        _require_equal(errors, leakage.get(key), True, f"splits.leakage.{key}")
    _require_equal(
        errors,
        leakage.get("allowed_known_leaks"),
        0,
        "splits.leakage.allowed_known_leaks",
    )

    privacy = documents["splits"].get("privacy", {})
    for key in (
        "opaque_public_ids",
        "private_reverse_mapping",
        "hide_test_labels",
        "hide_scoring_metadata",
    ):
        _require_equal(errors, privacy.get(key), True, f"splits.privacy.{key}")

    reporting = documents["evaluation"].get("reporting", {})
    _require_equal(
        errors,
        reporting.get("single_composite_is_primary"),
        False,
        "evaluation.reporting.single_composite_is_primary",
    )
    for key in (
        "report_by_task",
        "report_by_source",
        "report_id_ood",
        "report_cost_latency_failure",
        "report_physical_violation",
    ):
        _require_equal(errors, reporting.get(key), True, f"evaluation.reporting.{key}")
    _require_equal(
        errors,
        documents["evaluation"].get("failures", {}).get("manual_answer_repair"),
        False,
        "evaluation.failures.manual_answer_repair",
    )

    embargo = documents["embargo"].get("embargo", {})
    if embargo.get("state") not in {"PLANNED", "ACTIVE"}:
        errors.append(
            "test_embargo.embargo.state must be 'PLANNED' or 'ACTIVE', "
            f"got {embargo.get('state')!r}"
        )
    _require_equal(
        errors,
        embargo.get("activation_task"),
        "P2-FREEZE-001",
        "test_embargo.embargo.activation_task",
    )
    for key in (
        "developer_may_read_test_inputs",
        "developer_may_read_test_gold",
        "model_may_read_test_gold",
    ):
        _require_equal(errors, embargo.get(key), False, f"test_embargo.embargo.{key}")
    _require_equal(
        errors,
        embargo.get("access_ledger_required"),
        True,
        "test_embargo.embargo.access_ledger_required",
    )

    sources = documents["sources"].get("sources", [])
    source_tables = [source for source in sources if isinstance(source, dict)]
    if len(source_tables) != len(sources):
        errors.append("each data source must be a TOML table")
    ids = [source.get("id") for source in source_tables]
    if len(ids) != len(set(ids)):
        errors.append("data source IDs must be unique")
    if set(ids) != {f"D{index:02d}" for index in range(1, 12)}:
        errors.append("data_sources.toml must register exactly D01-D11")
    for source in source_tables:
        if source.get("id") in PLACEHOLDER_IDS:
            _require_equal(
                errors,
                source.get("eligible"),
                False,
                f"placeholder {source.get('id')}.eligible",
            )
            _require_equal(
                errors,
                source.get("state"),
                "ineligible_placeholder",
                f"placeholder {source.get('id')}.state",
            )

    for name, document in documents.items():
        for value in _iter_strings(document):
            if is_absolute_path_like(value):
                errors.append(f"personal absolute path in configs/{name}: {value!r}")

    try:
        current = _load_front_matter(root / "进度跟进记录/CURRENT_STATUS.md")
        next_prompt = _load_front_matter(root / "进度跟进记录/NEXT_SESSION_PROMPT.md")
        source_name = current.get("source_session", "")
        if Path(source_name).name != source_name or not source_name:
            errors.append("CURRENT_STATUS source_session must be one session-log filename")
        else:
            source_path = root / "进度跟进记录" / source_name
            if not source_path.is_file():
                errors.append(f"handoff source session does not exist: {source_name}")
            else:
                source_session = _load_front_matter(source_path)
                handoff_ids = {
                    current.get("handoff_id"),
                    next_prompt.get("handoff_id"),
                    source_session.get("handoff_id"),
                }
                states = {
                    current.get("handoff_state"),
                    next_prompt.get("handoff_state"),
                    source_session.get("handoff_state"),
                }
                current_tasks = {
                    current.get("current_task"),
                    next_prompt.get("current_task"),
                    source_session.get("next_task"),
                }
                source_names = {
                    current.get("source_session"),
                    next_prompt.get("source_session"),
                    source_name,
                }
                if len(handoff_ids) != 1 or None in handoff_ids:
                    errors.append("handoff IDs differ across current/session/next files")
                if states != {"READY"}:
                    errors.append("handoff states must all be READY")
                if len(current_tasks) != 1 or None in current_tasks:
                    errors.append("handoff current/next task IDs are inconsistent")
                if len(source_names) != 1:
                    errors.append("handoff source_session values are inconsistent")
    except (OSError, ValueError) as exc:
        errors.append(f"handoff metadata failure: {exc}")

    return errors
