"""CLI command mode for quick service access."""
import sys
import asyncio
import webbrowser
from typing import Optional

from .config import load_config, find_service_by_alias, ConfigError
from .api import RenderClient, RenderAPIError
from .models import ServiceConfig


class CLIError(Exception):
    """CLI error."""
    pass


def get_service_url(service_id: str, action: str) -> str:
    """Get Render dashboard URL for a service action.

    Args:
        service_id: Render service ID
        action: Action name (logs, events, settings, metrics)

    Returns:
        Full URL to Render dashboard
    """
    base_url = f"https://dashboard.render.com/web/{service_id}"

    if action == "logs":
        return f"{base_url}/logs"
    elif action == "events":
        return f"{base_url}/events"
    elif action == "metrics":
        return f"{base_url}/metrics"
    elif action == "settings":
        return base_url
    else:
        return base_url


async def get_service_status(service_config: ServiceConfig, api_key: str) -> str:
    """Get current status of a service.

    Args:
        service_config: Service configuration
        api_key: Render API key

    Returns:
        Formatted status string
    """
    from .utils import time_ago

    try:
        async with RenderClient(api_key) as client:
            service = await client.get_service_with_deploy(service_config.id)

            # Build status string with colored icons
            status_parts = []

            # Service status with appropriate icon
            if service.status.value == "available":
                status_icon = "🟢"  # Green for live
            elif service.status.value == "deploying":
                status_icon = "🟠"  # Orange for deploying
            elif service.status.value == "suspended":
                status_icon = "⚫"  # Gray for suspended
            elif service.status.value == "failed":
                status_icon = "🔴"  # Red for failed
            else:
                status_icon = "⚪"  # White for unknown

            status_parts.append(f"{status_icon} {service.name}")
            status_parts.append(f"Status: {service.status.value}")
            status_parts.append(f"Type: {service.type}")

            # Show custom domain (primary URL)
            if service.custom_domain:
                status_parts.append(f"URL: https://{service.custom_domain}")
            elif service.url:
                # Fallback to Render URL if no custom domain
                status_parts.append(f"URL: {service.url}")

            if service.latest_deploy:
                deploy = service.latest_deploy

                # Deploy status with icon
                if deploy.status.value == "live":
                    deploy_icon = "🟢"
                elif deploy.is_in_progress:
                    deploy_icon = "🟠"
                elif deploy.status.value == "build_failed":
                    deploy_icon = "🔴"
                else:
                    deploy_icon = "⚪"

                # Make deploy status clearer
                deploy_status_text = deploy.status.value.replace("_", " ").title()
                status_parts.append(f"Deployment: {deploy_icon} {deploy_status_text}")

                status_parts.append(f"Deployed: {time_ago(deploy.created_at)}")

                # Add GitHub commit link if available
                if deploy.commit_sha and deploy.repo_url:
                    commit_url = f"{deploy.repo_url}/commit/{deploy.commit_sha}"
                    status_parts.append(f"Commit: {deploy.commit_sha[:7]} - {commit_url}")

            return "\n".join(status_parts)

    except RenderAPIError as e:
        return f"Error fetching status: {e}"


def handle_cli_command(args: list[str]) -> int:
    """Handle CLI command mode.

    Args:
        args: Command line arguments (service alias and action)

    Returns:
        Exit code (0 for success, 1 for error)
    """
    if len(args) < 2:
        print("Usage: rdash <service> <action> [--no-browser]")
        print("")
        print("Actions:")
        print("  logs      - Open service logs in browser")
        print("  events    - Open service events in browser")
        print("  metrics   - Open service metrics in browser")
        print("  settings  - Open service settings in browser")
        print("  status    - Show current service status")
        print("")
        print("Options:")
        print("  --no-browser  Print URL without opening browser")
        print("")
        print("Examples:")
        print("  rdash chat logs")
        print("  rdash auth events")
        print("  rdash accounts status")
        print("  rdash chat logs --no-browser")
        return 1

    # Parse --no-browser flag
    no_browser = "--no-browser" in args
    args = [a for a in args if a != "--no-browser"]

    service_alias = args[0]
    action = args[1].lower() if len(args) > 1 else ""

    # Validate action
    valid_actions = ["logs", "events", "metrics", "settings", "status"]
    if action not in valid_actions:
        print(f"Invalid action: {action}")
        print(f"Valid actions: {', '.join(valid_actions)}")
        return 1

    # Load config
    try:
        config = load_config()
    except ConfigError as e:
        print(f"Configuration error: {e}")
        return 1

    # Find service
    try:
        service_config = find_service_by_alias(config, service_alias)
        if service_config is None:
            print(f"No service found matching '{service_alias}'")
            print("")
            print("Available services:")
            for svc in config.services:
                aliases = ", ".join(svc.aliases) if svc.aliases else "no aliases"
                print(f"  {svc.name} ({aliases})")
            return 1
    except ConfigError as e:
        print(str(e))
        return 1

    # Handle status action separately (doesn't open browser)
    if action == "status":
        status = asyncio.run(get_service_status(service_config, config.render.api_key))
        print(status)
        return 0

    # Get URL and open in browser (unless --no-browser)
    url = get_service_url(service_config.id, action)

    if no_browser:
        print(url)
        return 0

    try:
        webbrowser.open(url)
        print(f"Opening {action} for {service_config.name}...")
        print(f"URL: {url}")
        return 0
    except Exception as e:
        print(f"Failed to open browser: {e}")
        print(f"Open this URL manually: {url}")
        return 1
