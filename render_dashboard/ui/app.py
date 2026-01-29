"""Main Textual TUI application."""
import asyncio
import webbrowser
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Header, Footer, Static
from textual.binding import Binding

from ..config import AppConfig, load_config, ConfigError
from ..api import RenderClient, RenderAPIError
from ..models import Service
from .widgets import ServiceCard, StatusBar


class DashboardApp(App):
    """Render Services Dashboard TUI application."""

    CSS = """
    Screen {
        background: $surface;
    }

    #services-container {
        height: 1fr;
        padding: 1;
    }

    .error-message {
        color: red;
        padding: 1;
    }

    .loading-message {
        color: yellow;
        padding: 1;
    }
    """

    BINDINGS = [
        Binding("r", "refresh", "Refresh", show=True),
        Binding("q", "quit", "Quit", show=True),
        ("l", "action_logs", "Logs"),
        ("e", "action_events", "Events"),
        ("d", "action_deploys", "Deploys"),
        ("s", "action_settings", "Settings"),
    ]

    TITLE = "Render Services Dashboard"

    def __init__(self, config_path: Optional[str] = None, *args, **kwargs):
        """Initialize the dashboard app.

        Args:
            config_path: Optional path to config.yaml
        """
        super().__init__(*args, **kwargs)
        self.config_path = config_path
        self.config: Optional[AppConfig] = None
        self.service_cards: dict[str, ServiceCard] = {}
        self.refresh_task: Optional[asyncio.Task] = None

    def compose(self) -> ComposeResult:
        """Compose the UI layout."""
        yield Header()
        yield VerticalScroll(id="services-container")
        yield StatusBar()
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize the dashboard when mounted."""
        try:
            # Load configuration
            self.config = load_config(self.config_path)

            # Initial service load
            await self.refresh_services()

            # Start auto-refresh task
            self.refresh_task = asyncio.create_task(self._auto_refresh_loop())

        except ConfigError as e:
            self._show_error(f"Configuration error: {e}")
        except Exception as e:
            self._show_error(f"Unexpected error: {e}")

    async def on_unmount(self) -> None:
        """Clean up when unmounting."""
        if self.refresh_task:
            self.refresh_task.cancel()
            try:
                await self.refresh_task
            except asyncio.CancelledError:
                pass

    def _show_error(self, message: str) -> None:
        """Show an error message in the UI."""
        container = self.query_one("#services-container")
        container.mount(Static(message, classes="error-message"))

    def _show_loading(self) -> None:
        """Show loading message."""
        container = self.query_one("#services-container")
        container.remove_children()
        container.mount(Static("Loading services...", classes="loading-message"))

    async def refresh_services(self) -> None:
        """Fetch and update all services."""
        if not self.config:
            return

        try:
            async with RenderClient(self.config.render.api_key) as client:
                # Fetch all services concurrently
                tasks = [
                    client.get_service_with_deploy(svc.id)
                    for svc in self.config.services
                ]
                services = await asyncio.gather(*tasks, return_exceptions=True)

                # Update UI with results
                container = self.query_one("#services-container")

                for service_config, service_result in zip(self.config.services, services):
                    if isinstance(service_result, Exception):
                        # Handle error for this specific service
                        continue

                    service: Service = service_result

                    if service.id in self.service_cards:
                        # Update existing card
                        self.service_cards[service.id].update_service(service)
                    else:
                        # Create new card
                        card = ServiceCard(service)
                        self.service_cards[service.id] = card
                        container.mount(card)

                # Update status bar
                status_bar = self.query_one(StatusBar)
                status_bar.update_time()

        except RenderAPIError as e:
            self._show_error(f"API error: {e}")
        except Exception as e:
            self._show_error(f"Error refreshing services: {e}")

    async def _auto_refresh_loop(self) -> None:
        """Background task that auto-refreshes services."""
        if not self.config:
            return

        interval = self.config.render.refresh_interval

        try:
            while True:
                await asyncio.sleep(interval)
                await self.refresh_services()
        except asyncio.CancelledError:
            pass

    async def action_refresh(self) -> None:
        """Handle manual refresh action."""
        await self.refresh_services()

    def _get_focused_service_id(self) -> Optional[str]:
        """Get the service ID of the currently focused service card."""
        focused = self.focused
        if isinstance(focused, ServiceCard):
            return focused.service.id
        return None

    def _open_service_url(self, service_id: str, action: str) -> None:
        """Open a service URL in the browser.

        Args:
            service_id: Service ID
            action: Action (logs, events, deploys, settings)
        """
        from ..cli import get_service_url

        url = get_service_url(service_id, action)
        try:
            webbrowser.open(url)
        except Exception:
            # Silently fail - user can open manually
            pass

    async def on_service_card_service_selected(
        self, message: ServiceCard.ServiceSelected
    ) -> None:
        """Handle service action selection from ServiceCard."""
        self._open_service_url(message.service_id, message.action)

    def action_action_logs(self) -> None:
        """Open logs for focused service."""
        service_id = self._get_focused_service_id()
        if service_id:
            self._open_service_url(service_id, "logs")

    def action_action_events(self) -> None:
        """Open events for focused service."""
        service_id = self._get_focused_service_id()
        if service_id:
            self._open_service_url(service_id, "events")

    def action_action_deploys(self) -> None:
        """Open deploys for focused service."""
        service_id = self._get_focused_service_id()
        if service_id:
            self._open_service_url(service_id, "deploys")

    def action_action_settings(self) -> None:
        """Open settings for focused service."""
        service_id = self._get_focused_service_id()
        if service_id:
            self._open_service_url(service_id, "settings")


def run_dashboard(config_path: Optional[str] = None) -> int:
    """Run the dashboard TUI application.

    Args:
        config_path: Optional path to config.yaml

    Returns:
        Exit code
    """
    try:
        app = DashboardApp(config_path=config_path)
        app.run()
        return 0
    except Exception as e:
        print(f"Error starting dashboard: {e}")
        return 1
