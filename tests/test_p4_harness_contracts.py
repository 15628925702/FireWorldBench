from __future__ import annotations

import json
from pathlib import Path

from fireworldbench.harness import run_harness


def sample(split: str = "dev_id") -> dict:
    return {"sample_id": "FWB-v1-T1-A-case_1-x", "task": "T1-A", "split": split}


def test_harness_isolates_raw_response_and_records_hashes(tmp_path: Path) -> None:
    def adapter(item, prompt, config):
        return {"sample_id": item["sample_id"], "answer": {"label": "ok"}, "prompt_seen": prompt}

    result = run_harness([sample()], tmp_path / "run", adapter=adapter, prompt_template="Task {task} / {sample_id}")

    assert result["sample_count"] == 1
    assert result["private_raw_response"] is True
    assert len(result["prompt_hash"]) == 64
    assert (tmp_path / "run/private/raw_responses.jsonl").is_file()
    public = json.loads((tmp_path / "run/public/run_manifest.json").read_text(encoding="utf-8"))
    assert "prompt_seen" not in json.dumps(public)


def test_harness_retains_timeout_invalid_json_and_retries(tmp_path: Path) -> None:
    calls = {"count": 0}

    def adapter(item, prompt, config):
        calls["count"] += 1
        if calls["count"] == 1:
            return "not-json"
        return {"answer": {"label": "insufficient_information"}}

    result = run_harness([sample()], tmp_path / "run", adapter=adapter, max_retries=1)

    assert result["results"][0]["attempts"] == 2
    assert result["results"][0]["status"] == "refusal"


def test_harness_refuses_test_split_and_overwrite(tmp_path: Path) -> None:
    try:
        run_harness([sample("test_id")], tmp_path / "run")
    except ValueError as exc:
        assert "train_id" in str(exc)
    else:
        raise AssertionError("test split must be refused")
    output = tmp_path / "existing"
    output.mkdir()
    try:
        run_harness([sample()], output)
    except FileExistsError:
        pass
    else:
        raise AssertionError("existing run must not be overwritten")
