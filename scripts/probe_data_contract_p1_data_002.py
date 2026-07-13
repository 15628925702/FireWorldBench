"""Read-only structural probe for P1-DATA-002 evidence files.

This probe never writes to the external dataset directory.
"""

from __future__ import annotations

import csv
from pathlib import Path


def probe_csv(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    return {
        "path": path.as_posix(),
        "row_count_sampled": min(len(rows), 3),
        "columns_sampled": len(rows[0]) if rows else 0,
        "first_rows": rows[:3],
    }


def main() -> None:
    root = Path(__file__).resolve().parents[3] / "3.数据集"
    paths = sorted(root.glob("01_Immersed-Tunnel-CFD/CFD-Data/*.csv"))[:1]
    paths += sorted(root.glob("03_FDS-exp/**/*.csv"))[:1]
    for path in paths:
        print(probe_csv(path))


if __name__ == "__main__":
    main()
