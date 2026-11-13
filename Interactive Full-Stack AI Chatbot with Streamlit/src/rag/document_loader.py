import io
from dataclasses import dataclass, field
from typing import List, Dict, Any, BinaryIO
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter


@dataclass
class DocumentChunk:
    chunk_id: str
    page_content: str
    source: str
    page_number: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)


def extract_text_from_pdf(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
    """Extract page-by-page text from PDF bytes."""
    pages = []
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        for idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                pages.append({"text": text.strip(), "page": idx + 1, "source": filename})
    except Exception as e:
        print(f"Error reading PDF {filename}: {e}")
    return pages


def extract_text_from_txt(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
    """Extract text from TXT/MD/CSV bytes."""
    try:
        content = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        content = file_bytes.decode("latin-1", errors="ignore")
    return [{"text": content.strip(), "page": 1, "source": filename}] if content.strip() else []


def process_uploaded_files(
    uploaded_files: List[Any],
    chunk_size: int = 800,
    chunk_overlap: int = 120,
) -> List[DocumentChunk]:
    """
    Parse uploaded files (PDF, TXT, MD, CSV) and split into searchable DocumentChunks.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    all_chunks: List[DocumentChunk] = []

    for file in uploaded_files:
        filename = getattr(file, "name", "unknown_document")
        file_bytes = file.getvalue() if hasattr(file, "getvalue") else file.read()
        lower_name = filename.lower()

        raw_pages: List[Dict[str, Any]] = []
        if lower_name.endswith(".pdf"):
            raw_pages = extract_text_from_pdf(file_bytes, filename)
        else:
            raw_pages = extract_text_from_txt(file_bytes, filename)

        for page_data in raw_pages:
            chunks = text_splitter.split_text(page_data["text"])
            for idx, chunk_text in enumerate(chunks):
                chunk_id = f"{filename}_p{page_data['page']}_c{idx}"
                all_chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        page_content=chunk_text,
                        source=filename,
                        page_number=page_data["page"],
                        metadata={
                            "source": filename,
                            "page": page_data["page"],
                            "chunk_index": idx,
                        },
                    )
                )

    return all_chunks
