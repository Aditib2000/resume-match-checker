"""Extract plain text from resume/job description files (.txt, .pdf, .docx).

Supports both real file paths (CLI usage) and in-memory file-like objects
(e.g. Streamlit's UploadedFile) so the same parsing logic works for both
the CLI tool and the web app.
"""

from pathlib import Path


def extract_text_from_stream(file_obj, suffix: str) -> str:
    """Parse text from a file-like object (readable, seekable). suffix includes the dot, e.g. '.pdf'."""
    suffix = suffix.lower()

    if suffix == ".txt":
        content = file_obj.read()
        return content.decode("utf-8", errors="ignore") if isinstance(content, bytes) else content

    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(file_obj)
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if suffix == ".docx":
        import docx

        doc = docx.Document(file_obj)
        return "\n".join(p.text for p in doc.paragraphs)

    raise ValueError(f"Unsupported file type: {suffix}. Use .txt, .pdf, or .docx")


def extract_text(file_path: str) -> str:
    path = Path(file_path)
    suffix = path.suffix.lower()
    if suffix == ".txt":
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return extract_text_from_stream(f, suffix)
    with open(path, "rb") as f:
        return extract_text_from_stream(f, suffix)


def extract_text_from_upload(uploaded_file) -> str:
    """For Streamlit's UploadedFile objects, which carry their own .name."""
    suffix = Path(uploaded_file.name).suffix.lower()
    return extract_text_from_stream(uploaded_file, suffix)
