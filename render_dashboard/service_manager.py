"""Service discovery and config management commands."""
import asyncio
import sys
from typing import Optional

from .config import (
    load_config,
    add_service_to_config,
    remove_service_from_config,
    get_config_path,
    ConfigError
)
from .api import RenderClient, RenderAPIError
from .models import Service


async def search_and_add_service(search_term: str, api_key: str) -> int:
    """Search for services by name and add to config.

    Args:
        search_term: Name, partial name, or service ID to search for
        api_key: Render API key

    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Check if it looks like a service ID (starts with srv-)
    if search_term.startswith("srv-"):
        print(f"Looking up service ID: {search_term}...")
        print()

        try:
            async with RenderClient(api_key) as client:
                service = await client.get_service(search_term)

            print(f"Found: {service.name} ({service.id})")
            print()

            # Skip to alias prompt
            matches = [service]

        except RenderAPIError as e:
            print(f"Error fetching service: {e}")
            print()
            print("Make sure the service ID is correct.")
            print("You can find service IDs at https://dashboard.render.com")
            return 1
    else:
        print(f"Searching for services matching '{search_term}'...")
        print()

        async with RenderClient(api_key) as client:
            all_services = await client.list_services()

        if not all_services:
            print("No services found in your Render account.")
            print("Make sure you have services created at https://dashboard.render.com")
            print()
            print("If you know the service ID, you can add it directly:")
            print("  rdash service add srv-xxxxxxxxxxxxx")
            return 1

        # Filter services matching search term
        search_lower = search_term.lower()
        matches = [
            s for s in all_services
            if search_lower in s.name.lower() or search_lower in s.id.lower()
        ]

        if not matches:
            print(f"No services found matching '{search_term}'")
            print()
            print("Available services:")
            for service in all_services[:10]:  # Show first 10
                print(f"  - {service.name} ({service.id})")
            if len(all_services) > 10:
                print(f"  ... and {len(all_services) - 10} more")
            print()
            print("Or add by service ID directly:")
            print("  rdash service add srv-xxxxxxxxxxxxx")
            return 1

    # Show matches (used by both search and direct ID lookup)
    if len(matches) == 1:
        service = matches[0]
        if not search_term.startswith("srv-"):
            # Only print this if we searched (not direct ID lookup)
            print(f"Found: {service.name} ({service.id})")
            print()
    else:
        print(f"Found {len(matches)} matching services:")
        for i, service in enumerate(matches, 1):
            print(f"  {i}. {service.name} ({service.id}) - {service.type}")
        print()

        # Prompt user to select
        while True:
            try:
                choice = input(f"Select service (1-{len(matches)}, or 0 to cancel): ").strip()
                if choice == "0":
                    print("Cancelled")
                    return 0

                idx = int(choice) - 1
                if 0 <= idx < len(matches):
                    service = matches[idx]
                    break
                else:
                    print(f"Please enter a number between 1 and {len(matches)}")
            except ValueError:
                print("Please enter a valid number")
            except (KeyboardInterrupt, EOFError):
                print("\nCancelled")
                return 0

    # Get alias from user
    print()
    default_alias = service.name.lower().replace(" ", "-").replace("_", "-")
    alias_input = input(f"Enter alias for this service [{default_alias}]: ").strip()
    primary_alias = alias_input if alias_input else default_alias

    # Additional aliases
    additional = input("Additional aliases (comma-separated, or press Enter to skip): ").strip()
    aliases = [primary_alias]
    if additional:
        aliases.extend([a.strip() for a in additional.split(",") if a.strip()])

    # Add to config
    print()
    print(f"Adding {service.name} with aliases: {', '.join(aliases)}")

    try:
        add_service_to_config(
            service_id=service.id,
            service_name=service.name,
            aliases=aliases,
            priority=1
        )
        config_path = get_config_path()
        print(f"✓ Service added to {config_path}")
        print()
        print("You can now use:")
        for alias in aliases:
            print(f"  rdash {alias} logs")
            print(f"  rdash {alias} status")
        return 0

    except ConfigError as e:
        print(f"Error adding service: {e}")
        return 1


async def list_configured_services() -> int:
    """List services currently in config.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        config = load_config()
        print(f"Configured services ({len(config.services)}):")
        print()

        for service in sorted(config.services, key=lambda s: s.priority):
            aliases_str = ", ".join(service.aliases) if service.aliases else "no aliases"
            print(f"  {service.name}")
            print(f"    ID: {service.id}")
            print(f"    Aliases: {aliases_str}")
            print()

        return 0

    except ConfigError as e:
        print(f"Configuration error: {e}")
        return 1


async def remove_service_interactive(alias_or_id: str) -> int:
    """Remove a service from config.

    Args:
        alias_or_id: Service alias or ID to remove

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        config = load_config()

        # Find service by alias or ID
        service = None
        for s in config.services:
            if s.id == alias_or_id or alias_or_id.lower() in [a.lower() for a in s.aliases]:
                service = s
                break

        if not service:
            print(f"Service '{alias_or_id}' not found in config")
            return 1

        # Confirm removal
        print(f"Remove service: {service.name} ({service.id})?")
        confirm = input("Type 'yes' to confirm: ").strip().lower()

        if confirm != "yes":
            print("Cancelled")
            return 0

        remove_service_from_config(service.id)
        print(f"✓ Removed {service.name} from config")
        return 0

    except ConfigError as e:
        print(f"Configuration error: {e}")
        return 1


def handle_service_management(args: list[str]) -> int:
    """Handle service management commands.

    Args:
        args: Command arguments after 'rdash service'

    Returns:
        Exit code
    """
    if len(args) == 0:
        print("Usage: rdash service <command>")
        print()
        print("Commands:")
        print("  add <name>     - Search and add a service by name")
        print("  list           - List configured services")
        print("  remove <alias> - Remove a service from config")
        print()
        print("Examples:")
        print("  rdash service add chat")
        print("  rdash service list")
        print("  rdash service remove chat")
        return 1

    command = args[0].lower()

    if command == "add":
        if len(args) < 2:
            print("Usage: rdash service add <name|service-id>")
            print()
            print("Examples:")
            print("  rdash service add chat              # Search by name")
            print("  rdash service add srv-xxxxxxxxxxxxx # Add by ID directly")
            return 1

        search_term = args[1]

        # Get API key
        try:
            config = load_config(allow_empty_services=True)
            api_key = config.render.api_key
        except ConfigError as e:
            # If no config exists, try to get API key from environment
            import os
            api_key = os.getenv("RENDER_API_KEY")
            if not api_key:
                print(f"Configuration error: {e}")
                print()
                print("Make sure RENDER_API_KEY is set:")
                print("  export RENDER_API_KEY=rnd_xxxxx")
                return 1

        return asyncio.run(search_and_add_service(search_term, api_key))

    elif command == "list":
        return asyncio.run(list_configured_services())

    elif command == "remove":
        if len(args) < 2:
            print("Usage: rdash service remove <alias>")
            print()
            print("Example: rdash service remove chat")
            return 1

        alias_or_id = args[1]
        return asyncio.run(remove_service_interactive(alias_or_id))

    else:
        print(f"Unknown command: {command}")
        print()
        print("Available commands: add, list, remove")
        return 1
