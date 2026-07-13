from __future__ import annotations

import json
from pathlib import Path

from fireworldbench.paper_figures import assess_figure_export, write_figure_decision


def test_figures_are_blocked_without_frozen_source_data() -> None:
    result = assess_figure_export()

    assert result["status"] == "BLOCKED_NO_FIGURE_SOURCE"
    assert result["figure_data"] == []
    assert result["plot_specs"] == []
    assert result["rendered_pdf"] == []
    assert result["rendered_png"] == []
    assert result["styles"]["manual_points"] is False


def test_claims_matrix_without_run_ids_cannot_render_figures(tmp_path: Path) -> None:
    results = tmp_path / "claims.json"
    results.write_text('{"result_freeze_manifest": {"run_ids": []}}\n', encoding="utf-8")
    result = assess_figure_export(results)
    assert result["status"] == "BLOCKED_NO_FIGURE_SOURCE"
    assert "figure_source_has_no_run_ids" in result["blockers"]


def test_figure_decision_file_is_machine_readable(tmp_path: Path) -> None:
    output = tmp_path / "figures.json"
    result = write_figure_decision(output)
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == result["status"]
