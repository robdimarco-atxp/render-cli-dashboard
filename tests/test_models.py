"""Tests for data models."""
from datetime import datetime, timezone

from render_dashboard.models import (
    Service,
    Deploy,
    ServiceStatus,
    DeployStatus,
)


class TestDeploy:
    """Tests for Deploy model."""

    def test_is_in_progress_build(self):
        """Test is_in_progress for build_in_progress status."""
        deploy = Deploy(
            id="dep-1",
            status=DeployStatus.BUILD_IN_PROGRESS,
            created_at=datetime.now(timezone.utc),
        )
        assert deploy.is_in_progress is True

    def test_is_in_progress_update(self):
        """Test is_in_progress for update_in_progress status."""
        deploy = Deploy(
            id="dep-1",
            status=DeployStatus.UPDATE_IN_PROGRESS,
            created_at=datetime.now(timezone.utc),
        )
        assert deploy.is_in_progress is True

    def test_is_in_progress_created(self):
        """Test is_in_progress for created status."""
        deploy = Deploy(
            id="dep-1",
            status=DeployStatus.CREATED,
            created_at=datetime.now(timezone.utc),
        )
        assert deploy.is_in_progress is True

    def test_is_not_in_progress_live(self):
        """Test is_in_progress returns False for live status."""
        deploy = Deploy(
            id="dep-1",
            status=DeployStatus.LIVE,
            created_at=datetime.now(timezone.utc),
        )
        assert deploy.is_in_progress is False

    def test_is_not_in_progress_failed(self):
        """Test is_in_progress returns False for build_failed status."""
        deploy = Deploy(
            id="dep-1",
            status=DeployStatus.BUILD_FAILED,
            created_at=datetime.now(timezone.utc),
        )
        assert deploy.is_in_progress is False


class TestService:
    """Tests for Service model."""

    def test_status_emoji_available(self):
        """Test status emoji for available service."""
        service = Service(
            id="srv-1",
            name="Test",
            type="web_service",
            status=ServiceStatus.AVAILABLE,
        )
        assert service.get_status_emoji() == "●"

    def test_status_color_available(self):
        """Test status color for available service."""
        service = Service(
            id="srv-1",
            name="Test",
            type="web_service",
            status=ServiceStatus.AVAILABLE,
        )
        assert service.get_status_color() == "green"

    def test_status_color_deploying(self):
        """Test status color for deploying service."""
        service = Service(
            id="srv-1",
            name="Test",
            type="web_service",
            status=ServiceStatus.DEPLOYING,
        )
        assert service.get_status_color() == "yellow"

    def test_status_color_failed(self):
        """Test status color for failed service."""
        service = Service(
            id="srv-1",
            name="Test",
            type="web_service",
            status=ServiceStatus.FAILED,
        )
        assert service.get_status_color() == "red"
