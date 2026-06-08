import argparse
import os

import requests
from bs4 import BeautifulSoup

from .database import connect, upsert_document
from .pdf_processor import extract_text_and_tables
from .utils import configure_logging, json_log, rate_limit, retry_request, sha256_text


def extract_metadata(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    title = (soup.title.get_text(" ", strip=True) if soup.title else "Untitled")
    summary = " ".join([item.get_text(" ", strip=True) for item in soup.select("p, li")][:6])
    links = [a.get("href") for a in soup.select("a[href]") if a.get("href")]
    pdf_links = [link for link in links if link.lower().endswith(".pdf")]
    return {
        "url": url,
        "title": title,
        "date": None,
        "summary": summary[:500],
        "category": None,
        "pdf_url": pdf_links[0] if pdf_links else None,
        "hash": sha256_text(html),
        "source": url,
    }


def main(args: argparse.Namespace | None = None) -> None:
    configure_logging()
    parser = argparse.ArgumentParser(description="Parse discovered publication pages")
    parser.add_argument("--limit", type=int, default=10)
    ns = parser.parse_args() if args is None else args

    conn = connect()
    rows = conn.execute("SELECT url FROM documents ORDER BY id DESC LIMIT ?", (ns.limit,)).fetchall()
    for row in rows:
        url = row["url"]
        html = retry_request(lambda: requests.get(url, timeout=30).text)
        record = extract_metadata(html, url)
        upsert_document(conn, record)
        if record["pdf_url"]:
            try:
                extract_text_and_tables(record["pdf_url"], os.path.join("outputs", record["hash"][:8] + ".pdf"))
            except Exception as exc:
                json_log("pdf_parse_failed", url=url, error=str(exc))
        json_log("document_parsed", url=url, title=record["title"])
        rate_limit(1.0)
    print(f"Parsed {len(rows)} document rows")


if __name__ == "__main__":
    main()
