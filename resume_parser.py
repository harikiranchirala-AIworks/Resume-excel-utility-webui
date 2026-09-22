"""
resume_parser.py
Extracts text from .txt, .pdf, and .docx resume files.
"""
import io


def parse_resume(file_bytes: bytes, filename: str) -> str:
    """
    Parse resume file bytes into plain text.
    Supports: .txt, .pdf, .docx
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"

    if ext == "txt":
        return _parse_txt(file_bytes)
    elif ext == "pdf":
        return _parse_pdf(file_bytes)
    elif ext in ("docx", "doc"):
        return _parse_docx(file_bytes)
    else:
        raise ValueError(f"Unsupported file format: .{ext}. Please upload .txt, .pdf, or .docx")


def _parse_txt(data: bytes) -> str:
    for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            return data.decode(enc).strip()
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace").strip()


def _parse_pdf(data: bytes) -> str:
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text_parts.append(t)
        return "\n".join(text_parts).strip()
    except Exception as e:
        raise ValueError(f"Could not read PDF: {str(e)}")


def _parse_docx(data: bytes) -> str:
    try:
        from docx import Document
        doc = Document(io.BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip()).strip()
    except Exception as e:
        raise ValueError(f"Could not read DOCX: {str(e)}")
