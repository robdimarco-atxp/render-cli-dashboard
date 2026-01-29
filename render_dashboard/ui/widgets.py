"""Custom widgets for the TUI dashboard."""
from typing import Optional
from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Static, Label, OptionList
from textual.widgets.option_list import Option
from textual.message import Message
from textual.screen import ModalScreen
from datetime import datetime, timezone

from ..models import Service, EnvVar


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
            "[bold cyan]L[/]ogs | [bold cyan]E[/]vents | [bold cyan]M[/]etrics | En[bold cyan]v[/] | [bold cyan]S[/]ettings",
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

        # Build details string with commit hash if available
        if deploy.is_in_progress:
            details = f"└─ Deploy started: {time_ago}"
        else:
            details = f"└─ Last deploy: {time_ago} ({deploy.status.value})"

        # Add commit hash on a second line if available
        if deploy.commit_sha:
            short_sha = deploy.commit_sha[:7]
            details += f"\n   Commit: [cyan]{short_sha}[/]"
            if deploy.commit_message:
                # Truncate long commit messages
                msg = deploy.commit_message.split('\n')[0]  # First line only
                if len(msg) > 60:
                    msg = msg[:57] + "..."
                details += f" - {msg}"

        return details

    def update_service(self, service: Service) -> None:
        """Update the service data and refresh display.

        Args:
            service: Updated service data
        """
        self.service = service
        # Update existing widgets instead of recreating
        self._update_header_display()

        # Update details if they exist
        try:
            details = self.query_one(".service-details", Static)
            details.update(self._format_details())
        except Exception:
            # Details widget doesn't exist, skip
            pass

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
            "v": "env_vars",
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
        self.is_loading: bool = False

    def set_loading(self, loading: bool) -> None:
        """Set loading state."""
        self.is_loading = loading
        self._refresh_text()

    def update_time(self) -> None:
        """Update the last update timestamp."""
        self.last_update = datetime.now()
        self.is_loading = False
        self._refresh_text()

    def _refresh_text(self) -> None:
        """Refresh the status bar text."""
        if self.is_loading:
            text = "[bold yellow]⟳ Loading...[/]"
        elif self.last_update:
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


class EnvVarsScreen(ModalScreen):
    """Modal screen to display environment variables."""

    DEFAULT_CSS = """
    EnvVarsScreen {
        align: center middle;
    }

    #env-vars-container {
        width: 90;
        height: 35;
        border: heavy $primary;
        background: $surface;
    }

    #env-vars-header {
        dock: top;
        height: 3;
        background: $panel;
        content-align: center middle;
        text-style: bold;
    }

    #env-vars-list {
        height: 1fr;
        margin: 0 1;
        border: solid $primary-darken-1;
    }

    #env-var-detail {
        height: 6;
        background: $panel;
        border: solid $primary-darken-1;
        padding: 1;
        margin: 0 1;
    }

    #env-vars-footer {
        height: 1;
        background: $panel;
        content-align: center middle;
        padding: 0 1;
    }
    """

    BINDINGS = [
        ("escape", "dismiss", "Close"),
        ("q", "dismiss", "Close"),
        ("c", "copy_value", "Copy Value"),
        ("b", "open_browser", "Open in Browser"),
    ]

    def __init__(self, service_name: str, service_id: str, env_vars: list[EnvVar], error: Optional[str] = None, *args, **kwargs):
        """Initialize the env vars screen.

        Args:
            service_name: Name of the service
            service_id: Service ID for browser link
            env_vars: List of environment variables
            error: Optional error message to display
        """
        super().__init__(*args, **kwargs)
        self.service_name = service_name
        self.service_id = service_id
        self.env_vars = env_vars
        self.error = error

    def compose(self) -> ComposeResult:
        """Compose the modal layout."""
        with Container(id="env-vars-container"):
            yield Static(f"Environment Variables: {self.service_name} ({len(self.env_vars)} vars)", id="env-vars-header")

            if self.error:
                yield Static(f"[red]Error: {self.error}[/]", id="env-vars-list")
            elif not self.env_vars:
                yield Static("[yellow]No environment variables found[/]\n[dim]Press B to open in browser[/]", id="env-vars-list")
            else:
                # Create OptionList with env var names
                option_list = OptionList(id="env-vars-list")
                for env_var in self.env_vars:
                    option_list.add_option(Option(env_var.key, id=env_var.key))
                yield option_list

            if self.env_vars:
                yield Static("Select a variable and press [bold cyan]C[/] to copy", id="env-var-detail")

            if not self.env_vars and not self.error:
                yield Static("[bold]ESC[/] Close | [bold]B[/] Open in Browser", id="env-vars-footer")
            else:
                yield Static("[bold]ESC[/] Close | [bold]↑↓[/] Navigate | [bold]C[/] Copy | [bold]B[/] Browser", id="env-vars-footer")

    def on_mount(self) -> None:
        """When mounted, show first env var if available."""
        if self.env_vars:
            self._update_detail_panel()

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        """Handle option selection to show value."""
        self._update_detail_panel()

    def _update_detail_panel(self) -> None:
        """Update the detail panel with selected env var value."""
        try:
            option_list = self.query_one("#env-vars-list", OptionList)
            detail = self.query_one("#env-var-detail", Static)

            if option_list.highlighted is not None and self.env_vars:
                # Find the env var by index
                if option_list.highlighted < len(self.env_vars):
                    env_var = self.env_vars[option_list.highlighted]
                    # Show full value in detail panel
                    detail.update(f"[bold cyan]{env_var.key}[/]\n{env_var.value}")
                else:
                    detail.update("Select a variable")
            else:
                detail.update("Select a variable")
        except Exception:
            pass

    def action_copy_value(self) -> None:
        """Copy selected env var value to clipboard."""
        try:
            option_list = self.query_one("#env-vars-list", OptionList)
            detail = self.query_one("#env-var-detail", Static)

            if option_list.highlighted is not None and option_list.highlighted < len(self.env_vars):
                env_var = self.env_vars[option_list.highlighted]

                # Try to copy to clipboard using pbcopy (macOS) or xclip (Linux)
                import subprocess
                import platform

                try:
                    if platform.system() == "Darwin":
                        # macOS
                        process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
                        process.communicate(env_var.value.encode('utf-8'))
                        detail.update(f"[bold green]✓ Copied {env_var.key}[/]\n{env_var.value}")
                    elif platform.system() == "Linux":
                        # Linux
                        process = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE)
                        process.communicate(env_var.value.encode('utf-8'))
                        detail.update(f"[bold green]✓ Copied {env_var.key}[/]\n{env_var.value}")
                    else:
                        detail.update(f"[yellow]Copy not supported on {platform.system()}[/]\nValue: {env_var.value}")
                except FileNotFoundError:
                    detail.update(f"[yellow]Clipboard tool not found[/]\nValue: {env_var.value}")
        except Exception as e:
            self.log.error(f"Error copying: {e}")

    def action_dismiss(self) -> None:
        """Dismiss the modal."""
        self.app.pop_screen()

    def action_open_browser(self) -> None:
        """Open environment variables page in browser."""
        import webbrowser
        url = f"https://dashboard.render.com/web/{self.service_id}/env"
        try:
            webbrowser.open(url)
        except Exception:
            pass
        self.app.pop_screen()
