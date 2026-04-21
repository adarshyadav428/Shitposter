from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest

RUNS_TOTAL = Counter("newsbot_runs_total", "Total orchestrator run cycles")
RAW_EVENTS_TOTAL = Counter("newsbot_raw_events_total", "Total raw events observed")
ACCEPTED_EVENTS_TOTAL = Counter("newsbot_accepted_events_total", "Total accepted events")
PUBLISHED_EVENTS_TOTAL = Counter("newsbot_published_events_total", "Total published events")
DROPPED_EVENTS_TOTAL = Counter("newsbot_dropped_events_total", "Total dropped events")
DROPS_BY_REASON_TOTAL = Counter(
    "newsbot_drops_by_reason_total", "Dropped events by reason", ["reason"]
)
RETRACTIONS_TOTAL = Counter("newsbot_retractions_total", "Total retractions issued")
PUBLISH_FAILURES_TOTAL = Counter(
    "newsbot_publish_failures_total", "Total publish failures by channel", ["channel"]
)
AUTOPILOT_RUNNING = Gauge("newsbot_autopilot_running", "Autopilot runner state")
RETRACTION_MONITOR_RUNNING = Gauge(
    "newsbot_retraction_monitor_running", "Retraction monitor state"
)
HEARTBEAT_RUNNING = Gauge("newsbot_heartbeat_running", "Heartbeat runner state")
HEARTBEAT_FAILURES_TOTAL = Counter("newsbot_heartbeat_failures_total", "Total heartbeat failures")


def observe_run(stats: dict[str, int]) -> None:
    RUNS_TOTAL.inc(1)
    RAW_EVENTS_TOTAL.inc(stats.get("raw", 0))
    ACCEPTED_EVENTS_TOTAL.inc(stats.get("accepted", 0))
    PUBLISHED_EVENTS_TOTAL.inc(stats.get("published", 0))
    DROPPED_EVENTS_TOTAL.inc(stats.get("dropped", 0))


def observe_retractions(count: int = 1) -> None:
    if count > 0:
        RETRACTIONS_TOTAL.inc(count)


def observe_publish_failure(channel: str) -> None:
    PUBLISH_FAILURES_TOTAL.labels(channel=channel).inc(1)


def observe_drop_reason(reason: str) -> None:
    DROPS_BY_REASON_TOTAL.labels(reason=reason).inc(1)


def set_autopilot_running(running: bool) -> None:
    AUTOPILOT_RUNNING.set(1 if running else 0)


def set_retraction_monitor_running(running: bool) -> None:
    RETRACTION_MONITOR_RUNNING.set(1 if running else 0)


def set_heartbeat_running(running: bool) -> None:
    HEARTBEAT_RUNNING.set(1 if running else 0)


def observe_heartbeat_failure() -> None:
    HEARTBEAT_FAILURES_TOTAL.inc(1)


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
