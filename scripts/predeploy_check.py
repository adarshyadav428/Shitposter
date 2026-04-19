from __future__ import annotations

import json
import sys

from newsbot.config import Settings
from newsbot.preflight import evaluate_preflight


def main() -> int:
    report = evaluate_preflight(Settings())
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
