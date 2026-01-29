"""Main entry point for render-dashboard."""
import sys
from .cli import handle_cli_command
from .ui import run_dashboard


def main() -> int:
    """Main entry point that routes to CLI or TUI mode.

    If arguments are provided, runs in CLI mode (rd chat logs).
    If no arguments, runs TUI dashboard mode.

    Returns:
        Exit code
    """
    args = sys.argv[1:]

    if len(args) == 0:
        # No arguments - run TUI dashboard
        return run_dashboard()
    else:
        # Arguments provided - run CLI command
        return handle_cli_command(args)


if __name__ == "__main__":
    sys.exit(main())
