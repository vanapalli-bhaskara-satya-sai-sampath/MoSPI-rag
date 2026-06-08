from pathlib import Path

import pdfplumber

from .utils import ensure_parent, json_log


def extract_text_and_tables(pdf_url: str, output_path: str) -> dict:
    output = Path(output_path)
    ensure_parent(output)
    text_chunks = []
    try:
        with pdfplumber.open(pdf_url) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                text_chunks.append(text)
    except Exception as exc:
        json_log("pdf_text_extract_failed", pdf_url=pdf_url, error=str(exc))
        raise

    text_output = "\n\n".join(text_chunks)
    output.write_text(text_output, encoding="utf-8")
    return {"text_path": str(output), "text_length": len(text_output)}
