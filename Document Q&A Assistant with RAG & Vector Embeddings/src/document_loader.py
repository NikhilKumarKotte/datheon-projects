"""
Document loading module for PDF, TXT, and Markdown files.
Extracts document contents and standardizes metadata (page numbers, filenames, paths).
"""

import os
from pathlib import Path
from typing import List, Union, Optional
import logging
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentLoaderService:
    """Service to load documents from file paths, directories, or uploaded streams."""

    SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}

    @classmethod
    def load_file(cls, file_path: Union[str, Path]) -> List[Document]:
        """Loads a single document and enriches metadata.

        Args:
            file_path: Path to the target PDF or text file.

        Returns:
            List of LangChain Document objects with standardized metadata.
        """
        path = Path(file_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Document not found at path: {path}")

        ext = path.suffix.lower()
        if ext not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file format '{ext}'. Supported formats: {cls.SUPPORTED_EXTENSIONS}"
            )

        logger.info(f"Loading document: {path.name} ({ext})")
        docs: List[Document] = []

        try:
            if ext == ".pdf":
                loader = PyPDFLoader(str(path))
                raw_docs = loader.load()
                total_pages = len(raw_docs)
                for doc in raw_docs:
                    # PyPDFLoader page numbers are 0-indexed; convert to 1-indexed for human citations
                    raw_page = doc.metadata.get("page", 0)
                    page_num = int(raw_page) + 1 if isinstance(raw_page, (int, str)) and str(raw_page).isdigit() else 1
                    
                    doc.metadata["page"] = page_num
                    doc.metadata["file_name"] = path.name
                    doc.metadata["source"] = str(path)
                    doc.metadata["total_pages"] = total_pages
                    doc.metadata["file_type"] = "pdf"
                    docs.append(doc)
            elif ext in {".txt", ".md"}:
                loader = TextLoader(str(path), encoding="utf-8")
                raw_docs = loader.load()
                for doc in raw_docs:
                    doc.metadata["page"] = 1
                    doc.metadata["file_name"] = path.name
                    doc.metadata["source"] = str(path)
                    doc.metadata["total_pages"] = 1
                    doc.metadata["file_type"] = ext.lstrip(".")
                    docs.append(doc)
            
            logger.info(f"Successfully loaded {len(docs)} pages/sections from '{path.name}'.")
            return docs

        except Exception as e:
            logger.error(f"Failed to load document '{path.name}': {str(e)}")
            raise RuntimeError(f"Error loading {path.name}: {e}") from e

    @classmethod
    def load_directory(
        cls, directory_path: Union[str, Path], recursive: bool = True
    ) -> List[Document]:
        """Loads all supported documents from a directory.

        Args:
            directory_path: Directory path to scan.
            recursive: Whether to scan subdirectories.

        Returns:
            Aggregated list of Document objects.
        """
        dir_path = Path(directory_path).resolve()
        if not dir_path.is_dir():
            raise NotADirectoryError(f"Directory not found: {dir_path}")

        pattern = "**/*" if recursive else "*"
        all_docs: List[Document] = []

        for item in dir_path.glob(pattern):
            if item.is_file() and item.suffix.lower() in cls.SUPPORTED_EXTENSIONS:
                try:
                    file_docs = cls.load_file(item)
                    all_docs.extend(file_docs)
                except Exception as err:
                    logger.warning(f"Skipping problematic file '{item.name}': {err}")

        logger.info(f"Loaded total of {len(all_docs)} document pages from '{dir_path}'.")
        return all_docs

    @classmethod
    def save_and_load_uploaded_file(
        cls, file_bytes: bytes, file_name: str, target_dir: Path
    ) -> List[Document]:
        """Saves uploaded file bytes to target directory and returns loaded Document objects.

        Args:
            file_bytes: Raw binary content of the file.
            file_name: Original file name.
            target_dir: Directory where the file should be saved.

        Returns:
            List of Document objects.
        """
        target_dir.mkdir(parents=True, exist_ok=True)
        dest_path = target_dir / file_name
        dest_path.write_bytes(file_bytes)
        return cls.load_file(dest_path)
