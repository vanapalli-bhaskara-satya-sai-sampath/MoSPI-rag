import argparse
import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from .database import connect, upsert_document
from .utils import configure_logging, json_log, rate_limit, retry_request


API_URL = "https://www.mospi.gov.in/api/public-doc/get-web-pub-doc-list"
RAW_JSON_DIR = Path("data/raw/json")


def extract_listing_links(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    links = [a.get("href") for a in soup.select("a[href]") if a.get("href")]
    return [link for link in links if ".pdf" in link.lower() or "publication" in link.lower()]


def crawl_listing_page(url: str, limit: int = 10) -> list[dict]:
    if "api/public-doc/get-web-pub-doc-list" in url or url.startswith("https://www.mospi.gov.in/api/"):
        response = retry_request(lambda: requests.post(API_URL, json={"page": 1, "per_page": limit, "search": "", "start_date": "", "end_date": ""}, timeout=60))
        payload = response.json()
        items = payload.get("data", []) if isinstance(payload, dict) else []
        records = []
        for item in items[:limit]:
            file_one = item.get("file_one") or {}
            pdf_url = None
            if file_one.get("path"):
                pdf_url = "https://www.mospi.gov.in/" + file_one["path"]
            records.append({
                "url": pdf_url or f"https://www.mospi.gov.in/public-document?id={item.get('id')}",
                "title": item.get("title_en") or "Untitled",
                "date": item.get("published_year") or None,
                "summary": item.get("title_en") or None,
                "category": "public-document",
                "pdf_url": pdf_url,
                "hash": None,
                "source": url,
            })
            rate_limit(1.0)
        RAW_JSON_DIR.mkdir(parents=True, exist_ok=True)
        (RAW_JSON_DIR / "mospi_public_documents.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
        return records

    html = retry_request(lambda: requests.get(url, timeout=30).text)
    links = extract_listing_links(html)[:limit]
    records = []
    for link in links:
        records.append({
            "url": link,
            "title": link.split("/")[-1].replace("-", " ").title(),
            "date": None,
            "summary": None,
            "category": None,
            "pdf_url": link if link.lower().endswith(".pdf") else None,
            "hash": None,
            "source": url,
        })
        rate_limit(1.0)
    return records


def main(args: argparse.Namespace | None = None) -> None:
    configure_logging()
    parser = argparse.ArgumentParser(description="Crawl MoSPI publication listings")
    parser.add_argument("--url", default="https://mospi.gov.in/publications")
    parser.add_argument("--limit", type=int, default=10)
    ns = parser.parse_args() if args is None else args

    records = crawl_listing_page(ns.url, ns.limit)
    conn = connect()
    for record in records:
        upsert_document(conn, record)
        json_log("document_crawled", url=record["url"], title=record["title"])
    print(f"Stored {len(records)} records into scraper_data.sqlite3")


if __name__ == "__main__":
    main()
