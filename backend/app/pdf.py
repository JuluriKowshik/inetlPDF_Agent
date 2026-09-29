"""PDF text extraction (PyMuPDF) and page-preserving chunking."""

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 150


def extract_pages(file_bytes):
    """Returns [(page_number, text)] for every page. page_number starts at 1."""
    import fitz  # PyMuPDF, imported lazily

    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages = []
    for i, page in enumerate(doc):
        pages.append((i + 1, page.get_text("text").strip()))
    doc.close()
    return pages


def chunk_pages(pages, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Sliding-window chunks that never cross a page, so page citations stay exact."""
    chunks = []
    for page_no, text in pages:
        text = " ".join(text.split())
        if not text:
            continue
        start = 0
        while start < len(text):
            end = min(start + size, len(text))
            chunks.append({"page": page_no, "text": text[start:end]})
            if end == len(text):
                break
            start = end - overlap
    return chunks
