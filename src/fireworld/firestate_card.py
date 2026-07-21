"""Deterministic compact S-track FireState Card."""

from __future__ import annotations

from typing import Any


def build_card(data: dict[str, Any]) -> list[str]:
    rows = [row for row in data.get("rows", []) if isinstance(row, dict)]
    if not rows:
        return ["No tabular rows available."]
    first, last = rows[0], rows[-1]
    temperatures = {
        f"R{i}": float(last.get(f"T_R{i}", last.get(f"T_R{i}_CEILING", 20.0)))
        for i in range(1, 9)
    }
    visibility = {
        f"R{i}": float(last.get(f"V_R{i}", last.get(f"V_R{i}_CEILING", 30.0)))
        for i in range(1, 9)
    }
    hottest = max(temperatures, key=temperatures.__getitem__)
    lowest = min(visibility, key=visibility.__getitem__)
    temperature_delta = temperatures[hottest] - float(first.get(f"T_{hottest}", first.get(f"T_{hottest}_CEILING", 20.0)))
    visibility_delta = visibility[lowest] - float(first.get(f"V_{lowest}", first.get(f"V_{lowest}_CEILING", 30.0)))
    return [
        f"format={data.get('format', 'unknown')}",
        f"rows={len(rows)}",
        f"hottest_region={hottest}; temperature_c={temperatures[hottest]:.3f}; delta={temperature_delta:.3f}",
        f"lowest_visibility_region={lowest}; visibility_m={visibility[lowest]:.3f}; delta={visibility_delta:.3f}",
        f"max_temperature_c={max(temperatures.values()):.3f}",
        f"min_visibility_m={min(visibility.values()):.3f}",
    ]