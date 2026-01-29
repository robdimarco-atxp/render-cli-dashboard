"""Data models for Render services and deployments."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class ServiceStatus(str, Enum):
    """Service status values from Render API."""
    AVAILABLE = "available"
    DEPLOYING = "deploying"
    SUSPENDED = "suspended"
    FAILED = "failed"
    UNKNOWN = "unknown"


class DeployStatus(str, Enum):
    """Deploy status values from Render API."""
    LIVE = "live"
    BUILD_FAILED = "build_failed"
    CANCELED = "canceled"
    CREATED = "created"
    BUILD_IN_PROGRESS = "build_in_progress"
    UPDATE_IN_PROGRESS = "update_in_progress"
    DEACTIVATED = "deactivated"


@dataclass
class Deploy:
    """Represents a Render deployment."""
    id: str
    status: DeployStatus
    created_at: datetime
    finished_at: Optional[datetime] = None
    commit_sha: Optional[str] = None
    commit_message: Optional[str] = None
    repo_url: Optional[str] = None

    @property
    def is_in_progress(self) -> bool:
        """Check if deployment is currently in progress."""
        return self.status in (
            DeployStatus.BUILD_IN_PROGRESS,
            DeployStatus.UPDATE_IN_PROGRESS,
            DeployStatus.CREATED
        )


@dataclass
class Service:
    """Represents a Render service."""
    id: str
    name: str
    type: str  # web service, cron job, static site, etc.
    status: ServiceStatus
    url: Optional[str] = None
    custom_domain: Optional[str] = None
    latest_deploy: Optional[Deploy] = None

    def get_status_emoji(self) -> str:
        """Get emoji representation of service status."""
        if self.status == ServiceStatus.AVAILABLE:
            return "●"  # Green dot (will be colored in UI)
        elif self.status == ServiceStatus.DEPLOYING:
            return "●"  # Yellow dot
        elif self.status == ServiceStatus.FAILED:
            return "●"  # Red dot
        elif self.status == ServiceStatus.SUSPENDED:
            return "○"  # Gray hollow circle
        return "?"

    def get_status_color(self) -> str:
        """Get Textual color name for service status."""
        if self.status == ServiceStatus.AVAILABLE:
            return "green"
        elif self.status == ServiceStatus.DEPLOYING:
            return "yellow"
        elif self.status == ServiceStatus.FAILED:
            return "red"
        elif self.status == ServiceStatus.SUSPENDED:
            return "gray"
        return "white"


@dataclass
class ServiceConfig:
    """Configuration for a service from config.yaml."""
    id: str
    name: str
    aliases: list[str]
    priority: int = 1
