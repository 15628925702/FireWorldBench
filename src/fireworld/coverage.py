"""Machine-readable v2 task-track-source coverage report."""

from __future__ import annotations

from fireworld.contracts import SOURCES, TASKS, source_eligibility


def coverage_matrix() -> list[dict[str, str]]:
    return [
        {"source_domain": source, "task_id": task, "track": track,
         "eligibility": source_eligibility(source, task, track)}
        for source in sorted(SOURCES)
        for task in TASKS
        for track in ("S", "I", "V")
    ]
