import hashlib
import json
import logging
import random
import time
from pathlib import Path
from typing import Callable, TypeVar

import requests

T = TypeVar("T")


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def rate_limit(seconds: float = 2.0) -> None:
    time.sleep(seconds + random.uniform(0, 0.5))


def retry_request(fetcher: Callable[[], T], retries: int = 3, backoff: float = 1.0) -> T:
    last_exc = None
    for attempt in range(retries):
        try:
            return fetcher()
        except Exception as exc:  # pragma: no cover - simple retry wrapper
            last_exc = exc
            if attempt == retries - 1:
                raise
            time.sleep(backoff * (attempt + 1))
    raise last_exc


def json_log(event: str, **payload: object) -> None:
    logging.info(json.dumps({"event": event, **payload}, ensure_ascii=False))


def ensure_parent(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
