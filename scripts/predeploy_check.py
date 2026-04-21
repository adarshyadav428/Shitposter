from __future__ import annotations

import argparse
import json

from newsbot.config import Settings
from newsbot.preflight import evaluate_preflight


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run static deployment preflight checks")
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Path to env file to validate (default: .env)",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = evaluate_preflight(Settings(_env_file=args.env_file))
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
