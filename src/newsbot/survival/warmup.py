from datetime import datetime, timedelta, timezone


def account_is_warmed(account_created_at: datetime, required_days: int = 14) -> bool:
    now = datetime.now(timezone.utc)
    return now - account_created_at >= timedelta(days=required_days)
