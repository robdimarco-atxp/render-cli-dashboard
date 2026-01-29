"""Tests for utility functions."""
from datetime import datetime, timezone, timedelta

from render_dashboard.utils import time_ago


class TestTimeAgo:
    """Tests for time_ago function."""

    def test_seconds_ago(self):
        """Test formatting for recent times (seconds)."""
        dt = datetime.now(timezone.utc) - timedelta(seconds=30)
        assert time_ago(dt) == "30s ago"

    def test_minutes_ago(self):
        """Test formatting for minutes."""
        dt = datetime.now(timezone.utc) - timedelta(minutes=5)
        assert time_ago(dt) == "5m ago"

    def test_hours_ago(self):
        """Test formatting for hours."""
        dt = datetime.now(timezone.utc) - timedelta(hours=3)
        assert time_ago(dt) == "3h ago"

    def test_days_ago(self):
        """Test formatting for days."""
        dt = datetime.now(timezone.utc) - timedelta(days=2)
        assert time_ago(dt) == "2d ago"

    def test_naive_datetime_assumed_utc(self):
        """Test that naive datetimes are treated as UTC."""
        dt = datetime.utcnow() - timedelta(minutes=10)
        result = time_ago(dt)
        assert "m ago" in result

    def test_zero_seconds(self):
        """Test edge case of 0 seconds."""
        dt = datetime.now(timezone.utc)
        assert time_ago(dt) == "0s ago"
