import asyncio
from argparse import ArgumentParser
from sys import argv
from rich.console import Console
console = Console()

from sassy.core import run

def main() -> None:
    """
    """

    parser = ArgumentParser(
        description="Arguments for sassy"
    )

    if len(argv) == 1:
        parser.print_help()
        return
    
    parser.add_argument(
        "target",
        help="Specify the keyword to be used",
    )
    
    parser.add_argument(
        "--output",
        help="Specify the filename to save the output"
    )

    parser.add_argument(
        "--threads",
        help="Specify the number of threads to use",
        type=int,
        default=10
    )

    parser.add_argument(
        "--verbose",
        help="Enable verbose mode",
        action='store_true'
    )

    args = parser.parse_args()

    asyncio.run(run(
        target=args.target,
        output=args.output,
        threads=args.threads,
        verbose=args.verbose,
    ))