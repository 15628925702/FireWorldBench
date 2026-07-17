from __future__ import annotations

import argparse

from fireworld.contracts import TASKS


def main() -> int:
    parser = argparse.ArgumentParser(description="Build v2 QA from split-assigned Fire Events")
    parser.add_argument("--task", choices=sorted(TASKS), required=True)
    parser.add_argument("--tracks", required=True, help="Comma-separated subset of S,I,V")
    args = parser.parse_args()
    tracks = [item.strip() for item in args.tracks.split(",") if item.strip()]
    invalid = sorted(set(tracks) - {"S", "I", "V"})
    if not tracks or invalid:
        parser.error(f"invalid tracks: {invalid or tracks}")
    print(f"Task {args.task} protocol selected for tracks {','.join(tracks)}; no QA were written.")
    return 0


raise SystemExit(main())
