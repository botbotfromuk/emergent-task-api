"""Entry point for CLI: python -m tasks <command>"""

from tasks.wiring import cli_parser
from emergent.wire.compile.targets.cli import cli_run

if __name__ == "__main__":
    cli_run(cli_parser)
