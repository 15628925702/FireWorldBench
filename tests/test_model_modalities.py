from __future__ import annotations

import json

import pytest

from fireworld.model_runner import _prompt


def base_qa(track: str) -> dict:
    return {
        "qa_id": "FWQ-AAAAAAAAAAAA",
        "task_id": "L1-2",
        "track": track,
        "question": "q",
        "options": [{"id": "A", "content_ref": "candidate.png" if track == "I" else "candidate.json"}],
        "observation": {
            "structured": {"ref": "current.json"} if track == "S" else None,
            "images": ["current.png"] if track == "I" else None,
            "video": "clip.mp4" if track == "V" else None,
            "context": "c",
            "time_window_s": [0, 1],
        },
    }


def test_s_prompt_hydrates_observation_and_candidate(tmp_path) -> None:
    (tmp_path / "current.json").write_text(json.dumps({"rows": [1]}))
    (tmp_path / "candidate.json").write_text(json.dumps({"rows": [2]}))
    prompt = _prompt(base_qa("S"), tmp_path)
    assert isinstance(prompt, str)
    assert '"content": {"rows": [1]}' in prompt
    assert '"content": {"rows": [2]}' in prompt


def test_i_prompt_embeds_public_image_bytes(tmp_path) -> None:
    (tmp_path / "current.png").write_bytes(b"current")
    (tmp_path / "candidate.png").write_bytes(b"candidate")
    content = _prompt(base_qa("I"), tmp_path)
    assert isinstance(content, list)
    urls = [part["image_url"]["url"] for part in content if part["type"] == "image_url"]
    assert len(urls) == 2
    assert all(url.startswith("data:image/png;base64,") for url in urls)


def test_v_is_explicitly_unsupported(tmp_path) -> None:
    (tmp_path / "clip.mp4").write_bytes(b"video")
    with pytest.raises(ValueError, match="V track is unsupported"):
        _prompt(base_qa("V"), tmp_path)
def test_i_prompt_accepts_null_options(tmp_path) -> None:
    qa = base_qa("I")
    qa["options"] = None
    (tmp_path / "current.png").write_bytes(b"current")
    content = _prompt(qa, tmp_path)
    assert isinstance(content, list)
    assert len([part for part in content if part["type"] == "image_url"]) == 1