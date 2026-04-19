from __future__ import annotations

from newsbot.main import build_default_orchestrator


def main() -> None:
    orchestrator = build_default_orchestrator()
    print(orchestrator.circuit_breaker.status())


if __name__ == "__main__":
    main()
