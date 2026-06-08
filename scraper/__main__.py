import argparse

from .crawl import main as crawl_main
from .parse import main as parse_main
from .report import main as report_main


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MoSPI scraper CLI")
    subparsers = parser.add_subparsers(dest="command")

    crawl_parser = subparsers.add_parser("crawl", help="crawl listing pages")
    crawl_parser.add_argument("--url", default="https://mospi.gov.in/publications")
    crawl_parser.add_argument("--limit", type=int, default=10)
    crawl_parser.set_defaults(func=crawl_main)

    parse_parser = subparsers.add_parser("parse", help="parse discovered documents")
    parse_parser.add_argument("--limit", type=int, default=10)
    parse_parser.set_defaults(func=parse_main)

    report_parser = subparsers.add_parser("report", help="show report")
    report_parser.set_defaults(func=report_main)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()
