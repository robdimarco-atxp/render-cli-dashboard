"""Main Textual TUI application."""
import asyncio
import webbrowser
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Header, Footer, Static, Input
from textual.binding import Binding

from ..config import AppConfig, load_config, ConfigError
from ..api import RenderClient, RenderAPIError
from ..models import Service
from .widgets import ServiceCard, StatusBar, EnvVarsScreen


class DashboardApp(App):
    """Render Services Dashboard TUI application."""

    CSS = """
    Screen {
        background: $surface;
    }

    #services-container {
        height: 1fr;
        width: 100%;
        padding: 1;
    }

    #search-input {
        height: 0;
        margin: 0 1;
        padding: 0 1;
        border: solid $primary;
        background: $panel;
        overflow: hidden;
    }

    #search-input.visible {
        height: 3;
    }

    #search-input:focus {
        border: heavy yellow;
    }

    .error-message {
        color: red;
        padding: 1;
    }

    .loading-message {
        width: 100%;
        height: auto;
        padding: 4;
        margin: 2;
        text-align: center;
        text-style: bold;
        border: heavy yellow;
        background: $panel;
    }
    """

    BINDINGS = [
        Binding("r", "refresh", "Refresh", show=True),
        Binding("q", "quit", "Quit", show=True),
        Binding("/", "search", "Search", show=True, priority=True),
        Binding("escape", "cancel_search", "Cancel", show=False, priority=True),
        ("l", "action_logs", "Logs"),
        ("e", "action_events", "Events"),
        ("m", "action_metrics", "Metrics"),
        ("v", "action_env_vars", "Env Vars"),
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
        self.loading_animation_state: bool = False

    def compose(self) -> ComposeResult:
        """Compose the UI layout."""
        yield Header()
        search_input = Input(placeholder="Search services...", id="search-input")
        search_input.can_focus = False  # Not focusable until search is activated
        yield search_input
        yield VerticalScroll(id="services-container")
        yield StatusBar()
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize the dashboard when mounted."""
        # Show loading in status bar
        status_bar = self.query_one(StatusBar)
        status_bar.set_loading(True)

        try:
            # Load configuration
            self.config = load_config(self.config_path)

            # Initial service load
            await self.refresh_services()

            # Focus first service after loading
            if self.service_cards:
                first_card = next(iter(self.service_cards.values()))
                first_card.focus()

            # Start auto-refresh task
            self.refresh_task = asyncio.create_task(self._auto_refresh_loop())

        except ConfigError as e:
            status_bar.set_loading(False)
            self._show_error(f"Configuration error: {e}")
        except Exception as e:
            status_bar.set_loading(False)
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
        """Show loading message with animation."""
        container = self.query_one("#services-container")
        container.remove_children()
        loading_widget = Static("[bold yellow]⟳ Loading services...[/]", classes="loading-message", id="loading-message")
        container.mount(loading_widget)
        # Start loading animation
        self.loading_animation_state = False
        self.set_interval(0.15, self._update_loading_animation, name="loading_animation")

    def _update_loading_animation(self) -> None:
        """Update loading animation."""
        try:
            widget = self.query_one("#loading-message", Static)
            if self.loading_animation_state:
                widget.update("[bold yellow]⟳ Loading services...[/]")
            else:
                widget.update("[bold yellow]⟲ Loading services...[/]")
            self.loading_animation_state = not self.loading_animation_state
        except Exception:
            # Widget no longer exists, stop animation
            try:
                self.remove_timer("loading_animation")
            except Exception:
                pass

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

                # Stop loading animation if running
                try:
                    self.remove_timer("loading_animation")
                except Exception:
                    pass

                # Update UI with results
                container = self.query_one("#services-container")

                # Clear loading message if it exists
                try:
                    loading_msg = container.query_one("#loading-message")
                    loading_msg.remove()
                except Exception:
                    pass

                for service_config, service_result in zip(self.config.services, services):
                    if isinstance(service_result, Exception):
                        # Handle error for this specific service
                        # Remove the card if it exists (to avoid showing stale/empty data)
                        if service_config.id in self.service_cards:
                            card = self.service_cards[service_config.id]
                            card.remove()
                            del self.service_cards[service_config.id]
                        # Log the error (optional: could show error in UI instead)
                        self.log.error(f"Failed to load service {service_config.name}: {service_result}")
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
        if message.action == "env_vars":
            # Handle env vars specially - show modal instead of opening URL
            await self._show_env_vars(message.service_id)
        else:
            self._open_service_url(message.service_id, message.action)

    async def _show_env_vars(self, service_id: str) -> None:
        """Show environment variables modal for a service."""
        if not self.config:
            return

        # Find service name
        service_card = self.service_cards.get(service_id)
        if not service_card:
            return

        service_name = service_card.service.name
        env_vars = []
        error_msg = None

        try:
            # Fetch env vars from API
            async with RenderClient(self.config.render.api_key) as client:
                env_vars = await client.get_env_vars(service_id)
                self.log.info(f"Fetched {len(env_vars)} env vars for {service_name}")

        except RenderAPIError as e:
            error_msg = str(e)
            self.log.error(f"Failed to fetch env vars: {e}")
        except Exception as e:
            error_msg = str(e)
            self.log.error(f"Error showing env vars: {e}")

        # Show modal screen even if there was an error
        await self.push_screen(EnvVarsScreen(service_name, service_id, env_vars, error=error_msg))

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

    def action_action_metrics(self) -> None:
        """Open metrics for focused service."""
        service_id = self._get_focused_service_id()
        if service_id:
            self._open_service_url(service_id, "metrics")

    def action_action_settings(self) -> None:
        """Open settings for focused service."""
        service_id = self._get_focused_service_id()
        if service_id:
            self._open_service_url(service_id, "settings")

    async def action_action_env_vars(self) -> None:
        """Show environment variables for focused service."""
        service_id = self._get_focused_service_id()
        if service_id:
            await self._show_env_vars(service_id)

    async def action_search(self) -> None:
        """Show and focus the search input."""
        if not self.service_cards:
            return  # No services to search

        search_input = self.query_one("#search-input", Input)
        search_input.value = ""  # Clear any previous search

        # Make sure all services are visible
        for card in self.service_cards.values():
            card.styles.display = "block"

        search_input.add_class("visible")
        search_input.can_focus = True
        search_input.focus()

    def action_cancel_search(self) -> None:
        """Hide search and focus first service."""
        search_input = self.query_one("#search-input", Input)

        # Only act if search is visible
        if not search_input.has_class("visible"):
            return

        search_input.remove_class("visible")
        search_input.can_focus = False
        search_input.value = ""

        # Show all services
        for card in self.service_cards.values():
            card.styles.display = "block"

        # Focus first service card
        if self.service_cards:
            first_card = next(iter(self.service_cards.values()))
            first_card.focus()

    async def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        if event.input.id != "search-input":
            return

        if not self.service_cards:
            return  # No services to filter

        query = event.value.lower().strip()

        # If empty query, show all services
        if not query:
            for card in self.service_cards.values():
                card.styles.display = "block"
            return

        # Filter services by name
        for card in self.service_cards.values():
            matches = query in card.service.name.lower()
            card.styles.display = "block" if matches else "none"

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle search input submission (Enter key)."""
        if event.input.id != "search-input":
            return

        search_input = self.query_one("#search-input", Input)
        search_input.remove_class("visible")
        search_input.can_focus = False

        # Focus first visible service
        for card in self.service_cards.values():
            if card.styles.display == "block":
                card.focus()
                break



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
