from __future__ import annotations

import argparse
import json
from pathlib import Path

from fireworld.model_runner import run


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a model on a frozen v2 QA manifest")
    parser.add_argument("--model", required=True)
    parser.add_argument("--track", choices=["S", "I", "V"], required=True)
    parser.add_argument("--qa", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260720)
    parser.add_argument("--timeout-s", type=float, default=60.0)
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument("--api-base", default="https://openrouter.ai/api/v1")
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    parser.add_argument("--allow-network", action="store_true")
    args = parser.parse_args()
    result = run(args.qa, args.output_dir, args.model, args.track, args.api_base, args.api_key_env, args.seed, args.timeout_s, args.max_retries, args.allow_network)
    print(json.dumps(result, sort_keys=True))
    return 0


raise SystemExit(main())
