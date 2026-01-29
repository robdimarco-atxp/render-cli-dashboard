"""Configuration file parsing and validation."""
import os
import yaml
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from .models import ServiceConfig


@dataclass
class RenderConfig:
    """Render API configuration."""
    api_key: str
    refresh_interval: int = 30


@dataclass
class AppConfig:
    """Application configuration."""
    render: RenderConfig
    services: list[ServiceConfig]


class ConfigError(Exception):
    """Configuration error."""
    pass


def _substitute_env_vars(value: str) -> str:
    """Substitute environment variables in format ${VAR_NAME}."""
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        env_var = value[2:-1]
        env_value = os.getenv(env_var)
        if env_value is None:
            raise ConfigError(
                f"Environment variable {env_var} not set. "
                f"Please set it with: export {env_var}=your-value"
            )
        return env_value
    return value


def load_config(config_path: Optional[Path] = None, allow_empty_services: bool = False) -> AppConfig:
    """Load and validate configuration from YAML file.

    Args:
        config_path: Path to config.yaml. If None, looks in current directory
                    and then in ~/.config/render-dashboard/
        allow_empty_services: If True, allows empty services list (for initial setup)

    Returns:
        Validated AppConfig object

    Raises:
        ConfigError: If config is invalid or missing
    """
    if config_path is None:
        # Look in current directory first
        config_path = Path("config.yaml")
        if not config_path.exists():
            # Try home directory
            config_path = Path.home() / ".config" / "render-dashboard" / "config.yaml"

        if not config_path.exists():
            raise ConfigError(
                "No config.yaml found. Please create one in the current directory "
                "or in ~/.config/render-dashboard/.\n"
                "You can create a basic config with: rdash service add <service-name>"
            )

    if not config_path.exists():
        raise ConfigError(f"Config file not found: {config_path}")

    try:
        with open(config_path, "r") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in config file: {e}")

    if not isinstance(data, dict):
        raise ConfigError("Config file must contain a YAML dictionary")

    # Parse render config
    render_data = data.get("render", {})
    if not render_data:
        raise ConfigError("Missing 'render' section in config")

    api_key = _substitute_env_vars(render_data.get("api_key", ""))
    if not api_key:
        raise ConfigError(
            "Missing render.api_key in config. "
            "Set it to ${RENDER_API_KEY} and export RENDER_API_KEY=your-key"
        )

    render_config = RenderConfig(
        api_key=api_key,
        refresh_interval=render_data.get("refresh_interval", 30)
    )

    # Parse services
    services_data = data.get("services", [])
    if not services_data and not allow_empty_services:
        raise ConfigError(
            "No services configured. Add services with:\n"
            "  rdash service add <service-name>"
        )

    services = []
    for i, service_data in enumerate(services_data):
        if not isinstance(service_data, dict):
            raise ConfigError(f"Service at index {i} must be a dictionary")

        service_id = service_data.get("id")
        if not service_id:
            raise ConfigError(f"Service at index {i} missing required 'id' field")

        name = service_data.get("name", service_id)
        aliases = service_data.get("aliases", [])
        if not isinstance(aliases, list):
            raise ConfigError(f"Service {service_id}: 'aliases' must be a list")

        priority = service_data.get("priority", 1)

        services.append(ServiceConfig(
            id=service_id,
            name=name,
            aliases=aliases,
            priority=priority
        ))

    return AppConfig(render=render_config, services=services)


def find_service_by_alias(config: AppConfig, alias: str) -> Optional[ServiceConfig]:
    """Find a service by alias or name (case-insensitive, partial match).

    Returns:
        ServiceConfig if exactly one match found, None otherwise

    Raises:
        ConfigError: If multiple services match
    """
    alias_lower = alias.lower()
    matches = []

    for service in config.services:
        # Check exact alias match first
        if alias_lower in [a.lower() for a in service.aliases]:
            return service

        # Check partial matches in aliases and name
        for a in service.aliases:
            if alias_lower in a.lower():
                matches.append(service)
                break
        else:
            if alias_lower in service.name.lower():
                matches.append(service)

    if len(matches) == 0:
        return None
    elif len(matches) == 1:
        return matches[0]
    else:
        # Multiple matches - format error message
        match_list = "\n".join(
            f"  {i+1}. {s.name} (aliases: {', '.join(s.aliases)})"
            for i, s in enumerate(matches)
        )
        raise ConfigError(
            f"Multiple services match '{alias}':\n{match_list}\n\n"
            f"Use a more specific alias or service name."
        )


def get_config_path() -> Path:
    """Get the path to config file (checking standard locations).

    Returns:
        Path to config file, or default location if not found
    """
    # Check current directory first
    config_path = Path("config.yaml")
    if config_path.exists():
        return config_path

    # Check home directory
    config_path = Path.home() / ".config" / "render-dashboard" / "config.yaml"
    if config_path.exists():
        return config_path

    # Default to current directory for new configs
    return Path("config.yaml")


def add_service_to_config(
    service_id: str,
    service_name: str,
    aliases: list[str],
    priority: int = 1,
    config_path: Optional[Path] = None
) -> None:
    """Add a new service to the config file.

    Args:
        service_id: Render service ID
        service_name: Display name for service
        aliases: List of aliases for CLI access
        priority: Display priority (default 1)
        config_path: Path to config file (uses default locations if None)

    Raises:
        ConfigError: If config file issues occur
    """
    if config_path is None:
        config_path = get_config_path()

    # Load existing config or create new one
    if config_path.exists():
        with open(config_path, "r") as f:
            data = yaml.safe_load(f) or {}
    else:
        # Create parent directory if needed
        config_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "render": {
                "api_key": "${RENDER_API_KEY}",
                "refresh_interval": 30
            },
            "services": []
        }

    # Check if service already exists
    services = data.get("services", [])
    for service in services:
        if service.get("id") == service_id:
            raise ConfigError(f"Service {service_id} already exists in config")

    # Add new service
    new_service = {
        "id": service_id,
        "name": service_name,
        "aliases": aliases,
        "priority": priority
    }
    services.append(new_service)
    data["services"] = services

    # Write back to file
    with open(config_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def remove_service_from_config(
    service_id: str,
    config_path: Optional[Path] = None
) -> None:
    """Remove a service from the config file.

    Args:
        service_id: Render service ID to remove
        config_path: Path to config file (uses default locations if None)

    Raises:
        ConfigError: If service not found or config file issues
    """
    if config_path is None:
        config_path = get_config_path()

    if not config_path.exists():
        raise ConfigError("No config file found")

    with open(config_path, "r") as f:
        data = yaml.safe_load(f) or {}

    services = data.get("services", [])
    original_length = len(services)

    # Remove service with matching ID
    services = [s for s in services if s.get("id") != service_id]

    if len(services) == original_length:
        raise ConfigError(f"Service {service_id} not found in config")

    data["services"] = services

    # Write back to file
    with open(config_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
