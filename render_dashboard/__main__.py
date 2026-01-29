"""Main entry point for render-dashboard."""
import sys
from .cli import handle_cli_command
from .ui import run_dashboard
from .service_manager import handle_service_management


def main() -> int:
    """Main entry point that routes to CLI or TUI mode.

    Routes:
    - No arguments: TUI dashboard mode
    - 'service' subcommand: Service management (add, list, remove)
    - Other arguments: CLI command mode (rd <service> <action>)

    Returns:
        Exit code
    """
    args = sys.argv[1:]

    if len(args) == 0:
        # No arguments - run TUI dashboard
        return run_dashboard()
    elif args[0] == "service":
        # Service management commands
        return handle_service_management(args[1:])
    else:
        # CLI command mode (rd <service> <action>)
        return handle_cli_command(args)


if __name__ == "__main__":
    sys.exit(main())
