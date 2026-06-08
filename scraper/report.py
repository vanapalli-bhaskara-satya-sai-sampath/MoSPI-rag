import argparse

from .database import connect, count_documents
from .utils import configure_logging


def build_summary() -> str:
    conn = connect()
    total = count_documents(conn)
    return f"Documents in database: {total}\n"


def main(args: argparse.Namespace | None = None) -> None:
    configure_logging()
    parser = argparse.ArgumentParser(description="Generate MoSPI scraper report")
    parser.parse_args() if args is None else args
    print(build_summary())


if __name__ == "__main__":
    main()
