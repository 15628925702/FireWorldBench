from pathlib import Path

from fireworldbench.llm_baseline import LLMConfig, run_llm_pilot
from fireworldbench.planning_pilot import build_planning_t1_pilot


def _sample() -> dict:
    return {
        "sample_id": "FWB-v1-T1-A-case_1-x",
        "task": "T1-A",
        "split": "dev_id",
        "question": {"prompt": "Visible numeric data only."},
        "observations": [{"observation_id": "obs_1", "modality": "sensor_table", "time_range_s": [0, 1], "quality": "valid", "units": {"time": "s"}, "visible_fields": ["HRR"]}],
        "answer": {"label": "fire_forming", "private_marker": "secret_gold"},
    }


def test_llm_pilot_exports_schema_predictions_without_exposing_gold() -> None:
    seen: dict[str, str] = {}

    def adapter(sample, prompt, config):
        seen["prompt"] = prompt
        return {"answer": {"label": "fire_forming"}, "evidence": ["obs_1"], "uncertainty": {"level": "low", "reason": "visible signal"}, "missing_information": []}

    config = LLMConfig(track="text_only_table", prompt_id="text_table_v1", model_id="deepseek-chat", approved=True)
    result = run_llm_pilot([_sample()], config, adapter=adapter)

    assert result["predictions"][0]["sample_id"] == "FWB-v1-T1-A-case_1-x"
    assert result["predictions"][0]["answer"]["label"] == "fire_forming"
    assert "secret_gold" not in seen["prompt"]
    assert "Allowed label values" in seen["prompt"]
    assert len(seen["prompt"]) < 4000


def test_planning_pilot_builds_small_read_only_t1_chain(tmp_path: Path) -> None:
    source = tmp_path / "data" / "raw" / "D01_Immersed-Tunnel-CFD"
    source.mkdir(parents=True)
    csv_path = source / "case.csv"
    csv_path.write_text("s,kW/m2\nTime,HRRPUA\n0,1\n1,2\n2,3\n", encoding="utf-8")
    before = csv_path.read_bytes()

    result = build_planning_t1_pilot(tmp_path, max_cases=1, rows_per_case=3)

    assert result["sample_count"] == 2
    assert result["record_count"] == 3
    assert result["samples"][0]["split"] == "dev_id"
    assert "Visible measurement rows" in result["samples"][0]["question"]["prompt"]
    assert csv_path.read_bytes() == before
