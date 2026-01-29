"""Custom widgets for the TUI dashboard."""
from typing import Optional
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static, Label
from textual.message import Message
from datetime import datetime, timezone

from ..models import Service


class ServiceCard(Container):
    """Widget displaying a single service's status."""

    DEFAULT_CSS = """
    ServiceCard {
        height: auto;
        border: solid $primary;
        margin: 1;
        padding: 1;
        background: $surface;
    }

    ServiceCard:focus {
        border: heavy yellow;
        background: $panel;
    }

    ServiceCard > .service-header {
        width: 100%;
        height: 1;
    }

    ServiceCard > .service-details {
        width: 100%;
        height: auto;
        color: $text-muted;
    }

    ServiceCard > .service-actions {
        width: 100%;
        height: 1;
        color: $text-muted;
    }

    ServiceCard:focus > .service-actions {
        color: yellow;
        text-style: bold;
    }
    """

    class ServiceSelected(Message):
        """Posted when a service is selected for action."""

        def __init__(self, service_id: str, action: str) -> None:
            self.service_id = service_id
            self.action = action
            super().__init__()

    def __init__(self, service: Service, *args, **kwargs) -> None:
        """Initialize service card.

        Args:
            service: Service to display
        """
        super().__init__(*args, **kwargs)
        self.service = service
        self.can_focus = True

    def compose(self) -> ComposeResult:
        """Compose the service card layout."""
        # Header with name and status
        status_emoji = self.service.get_status_emoji()

        # Map status to Rich color names
        status_colors = {
            "available": "green",
            "deploying": "yellow",
            "failed": "red",
            "suspended": "bright_black",
            "unknown": "white"
        }
        status_color = status_colors.get(self.service.status.value, "white")

        header_text = f"{self.service.name}"
        status_text = f"[{status_color}]{status_emoji} {self.service.status.value.title()}[/]"

        yield Static(
            f"{header_text}  {status_text}  [dim]{self.service.id}[/]",
            classes="service-header",
            id="header"
        )

        # Details line (deploy info)
        details = self._format_details()
        if details:
            yield Static(details, classes="service-details")

        # Actions (highlight action keys without brackets to avoid markup issues)
        yield Static(
            "[bold cyan]L[/]ogs | [bold cyan]E[/]vents | [bold cyan]M[/]etrics | [bold cyan]S[/]ettings",
            classes="service-actions"
        )

    def _format_details(self) -> str:
        """Format deploy details line."""
        if not self.service.latest_deploy:
            return "└─ No deployments"

        deploy = self.service.latest_deploy

        # Calculate time since deploy
        now = datetime.now(timezone.utc)
        if deploy.created_at.tzinfo is None:
            created_at = deploy.created_at.replace(tzinfo=timezone.utc)
        else:
            created_at = deploy.created_at

        delta = now - created_at
        if delta.days > 0:
            time_ago = f"{delta.days}d ago"
        elif delta.seconds >= 3600:
            time_ago = f"{delta.seconds // 3600}h ago"
        elif delta.seconds >= 60:
            time_ago = f"{delta.seconds // 60}m ago"
        else:
            time_ago = f"{delta.seconds}s ago"

        if deploy.is_in_progress:
            return f"└─ Deploy started: {time_ago}"
        else:
            return f"└─ Last deploy: {time_ago} ({deploy.status.value})"

    def update_service(self, service: Service) -> None:
        """Update the service data and refresh display.

        Args:
            service: Updated service data
        """
        self.service = service
        # Clear and re-compose
        self.remove_children()
        self.mount_all(self.compose())

    def _update_header_display(self) -> None:
        """Update header with selection indicator."""
        # Check if widget is mounted and has children
        try:
            header = self.query_one("#header", Static)
        except Exception:
            # Widget not ready yet, skip update
            return

        status_emoji = self.service.get_status_emoji()
        status_colors = {
            "available": "green",
            "deploying": "yellow",
            "failed": "red",
            "suspended": "bright_black",
            "unknown": "white"
        }
        status_color = status_colors.get(self.service.status.value, "white")
        status_text = f"[{status_color}]{status_emoji} {self.service.status.value.title()}[/]"

        # Add selection indicator when focused
        if self.has_focus:
            indicator = "[bold yellow]▶[/] "
        else:
            indicator = "  "

        header.update(
            f"{indicator}{self.service.name}  {status_text}  [dim]{self.service.id}[/]"
        )

    def on_mount(self) -> None:
        """Called when widget is mounted."""
        # Initial display update
        self._update_header_display()

    def on_focus(self) -> None:
        """Handle focus event."""
        self._update_header_display()

    def on_blur(self) -> None:
        """Handle blur event."""
        self._update_header_display()

    async def on_key(self, event) -> None:
        """Handle key presses when focused."""
        key = event.key.lower()

        action_map = {
            "l": "logs",
            "e": "events",
            "m": "metrics",
            "s": "settings",
        }

        if key in action_map:
            self.post_message(
                self.ServiceSelected(self.service.id, action_map[key])
            )
            event.prevent_default()
            event.stop()


class StatusBar(Static):
    """Status bar showing last update time and controls."""

    DEFAULT_CSS = """
    StatusBar {
        dock: bottom;
        height: 1;
        background: $panel;
        color: $text;
    }
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__("", *args, **kwargs)
        self.last_update: Optional[datetime] = None

    def update_time(self) -> None:
        """Update the last update timestamp."""
        self.last_update = datetime.now()
        self._refresh_text()

    def _refresh_text(self) -> None:
        """Refresh the status bar text."""
        if self.last_update:
            now = datetime.now()
            delta = now - self.last_update
            seconds_ago = int(delta.total_seconds())

            if seconds_ago < 60:
                time_str = f"{seconds_ago}s ago"
            else:
                time_str = f"{seconds_ago // 60}m ago"

            # Show brief "refreshing..." indicator for 2 seconds after update
            if seconds_ago < 2:
                text = f"[bold green]✓ Refreshed[/] {time_str}"
            else:
                text = f"Updated: {time_str}"
        else:
            text = "Loading..."

        controls = "[bold cyan]R[/] Refresh | [bold cyan]Q[/] Quit | Auto-refresh: 30s"
        # Pad to full width
        self.update(f" {text}  |  {controls}")

    def on_mount(self) -> None:
        """Set up periodic refresh of time display."""
        self.set_interval(1.0, self._refresh_text)
