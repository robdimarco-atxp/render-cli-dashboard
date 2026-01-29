"""Shared utility functions."""
from datetime import datetime, timezone


def time_ago(dt: datetime) -> str:
    """Format a datetime as a human-readable 'X ago' string.

    Args:
        dt: Datetime to format (naive datetimes assumed UTC)

    Returns:
        Human-readable time string like "5m ago", "2h ago", "3d ago"
    """
    now = datetime.now(timezone.utc)

    # Make naive datetime aware (assume UTC)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    delta = now - dt

    if delta.days > 0:
        return f"{delta.days}d ago"
    elif delta.seconds >= 3600:
        return f"{delta.seconds // 3600}h ago"
    elif delta.seconds >= 60:
        return f"{delta.seconds // 60}m ago"
    else:
        return f"{delta.seconds}s ago"
