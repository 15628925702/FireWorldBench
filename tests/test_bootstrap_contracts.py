from __future__ import annotations

import hashlib
import json
import tomllib
from copy import deepcopy
from pathlib import Path

import jsonschema
import pytest

from fireworldbench.project_checks import (
    discover_project_root,
    is_absolute_path_like,
    validate_project,
)

ROOT = Path(__file__).resolve().parents[1]


def load_json(relative: str) -> object:
    with (ROOT / relative).open(encoding="utf-8") as handle:
        return json.load(handle)


def test_sample_fixture_matches_schema() -> None:
    schema = load_json("schemas/benchmark_sample.schema.json")
    sample = load_json("tests/fixtures/minimal_sample.json")
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.validate(sample, schema)


def test_sample_schema_rejects_non_string_source_id() -> None:
    schema = load_json("schemas/benchmark_sample.schema.json")
    sample = deepcopy(load_json("tests/fixtures/minimal_sample.json"))
    assert isinstance(sample, dict)
    sample["provenance"]["source_id"] = 1
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(sample, schema)


def test_prediction_fixture_matches_schema() -> None:
    schema = load_json("schemas/prediction.schema.json")
    prediction = load_json("tests/fixtures/minimal_prediction.json")
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.validate(prediction, schema)


def test_placeholders_are_machine_ineligible() -> None:
    with (ROOT / "configs/data_sources.toml").open("rb") as handle:
        sources = tomllib.load(handle)["sources"]
    by_id = {source["id"]: source for source in sources}
    for source_id in ("D07", "D08", "D09", "D11"):
        assert by_id[source_id]["eligible"] is False
        assert by_id[source_id]["state"] == "ineligible_placeholder"


def test_split_is_group_first() -> None:
    with (ROOT / "configs/splits.toml").open("rb") as handle:
        config = tomllib.load(handle)
    assert config["split"]["strategy"] == "group_first"
    assert config["split"]["split_before_windowing"] is True
    assert config["leakage"]["allowed_known_leaks"] == 0


def test_core_design_pdf_is_frozen() -> None:
    path = ROOT / "开发要求约束/FireWorldBench_Benchmark_Design_v2.pdf"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == "16b4caec881825b8a8d41556a5abe6a428ae77944c98c45e56789add54c8d7ce"


def test_shared_project_validation_passes() -> None:
    assert discover_project_root(ROOT / "src/fireworldbench") == ROOT
    assert validate_project(ROOT) == []


@pytest.mark.parametrize(
    "value",
    [r"C:\\Users\\name\\data", r"\\server\\share\\data", "/home/name/data", "~/data"],
)
def test_absolute_path_detection(value: str) -> None:
    assert is_absolute_path_like(value)


def test_absolute_path_detection_allows_relative_paths_and_urls() -> None:
    assert not is_absolute_path_like("01_Immersed-Tunnel-CFD")
    assert not is_absolute_path_like("https://example.invalid/data")
