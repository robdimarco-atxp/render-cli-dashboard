"""Main entry point for render-dashboard."""
import sys
from pathlib import Path
from typing import Optional
from .cli import handle_cli_command
from .ui import run_dashboard
from .service_manager import handle_service_management


def extract_config_arg(args: list[str]) -> tuple[Optional[Path], list[str]]:
    """Extract --config argument from args list.

    Args:
        args: Command line arguments

    Returns:
        Tuple of (config_path, remaining_args)
    """
    config_path = None
    remaining_args = []
    i = 0

    while i < len(args):
        if args[i] == "--config" and i + 1 < len(args):
            config_path = Path(args[i + 1])
            i += 2  # Skip both --config and its value
        else:
            remaining_args.append(args[i])
            i += 1

    return config_path, remaining_args


def main() -> int:
    """Main entry point that routes to CLI or TUI mode.

    Routes:
    - No arguments: TUI dashboard mode
    - 'service' subcommand: Service management (add, list, remove)
    - Other arguments: CLI command mode (rdash <service> <action>)

    Global options:
    - --config <path>: Specify config file location

    Returns:
        Exit code
    """
    args = sys.argv[1:]

    # Extract --config argument
    config_path, args = extract_config_arg(args)

    if len(args) == 0:
        # No arguments - run TUI dashboard
        return run_dashboard(config_path=config_path)
    elif args[0] == "service":
        # Service management commands
        return handle_service_management(args[1:], config_path=config_path)
    else:
        # CLI command mode (rdash <service> <action>)
        return handle_cli_command(args, config_path=config_path)


if __name__ == "__main__":
    sys.exit(main())
