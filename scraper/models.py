from pydantic import BaseModel, Field
from typing import List, Optional


class DocumentRecord(BaseModel):
    url: str
    title: str
    date: Optional[str] = None
    summary: Optional[str] = None
    category: Optional[str] = None
    pdf_url: Optional[str] = None
    hash: Optional[str] = None
    source: Optional[str] = None


class FileMetadata(BaseModel):
    document_url: str
    local_path: str
    sha256: str
    mime_type: Optional[str] = None


class TabularData(BaseModel):
    document_url: str
    csv_path: str
    pages: List[int] = Field(default_factory=list)
