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

    parser.add_argument(
        "-s", "--service",
        help="Specify one or more services to check (use service name from services.yaml)",
        action='append',
        dest='services'
    )

    parser.add_argument(
        "-f", "--follow-redirects",
        help="Follow HTTP redirects",
        action='store_true',
        dest='follow_redirects'
    )

    args = parser.parse_args()

    services = None
    if args.services:
        services = []
        for service in args.services:
            services.extend(service.split(','))

    asyncio.run(run(
        target=args.target,
        output=args.output,
        threads=args.threads,
        verbose=args.verbose,
        services=services,
        follow_redirects=args.follow_redirects,
    ))