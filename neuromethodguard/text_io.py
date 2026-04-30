from __future__ import annotations

from pathlib import Path


def read_text_file(path: str | Path) -> str:
    """Read .txt/.md/.pdf/.docx input into plain text.

    The function intentionally avoids OCR. It extracts embedded text only.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".markdown", ".rst"}:
        return path.read_text(encoding="utf-8", errors="ignore")

    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        parts: list[str] = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            parts.append(f"\n\n--- page {i + 1} ---\n{page_text}")
        return "\n".join(parts)

    if suffix == ".docx":
        from docx import Document

        doc = Document(str(path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)

    raise ValueError(
        f"Unsupported file type: {suffix}. Supported: .txt, .md, .pdf, .docx"
    )
