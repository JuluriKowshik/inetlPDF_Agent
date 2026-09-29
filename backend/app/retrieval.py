"""Per-document BM25 retrieval with a lazy in-memory index cache."""
from . import db
from .bm25 import BM25Index

_cache = {}


def _index_for(document_id):
    entry = _cache.get(document_id)
    if entry is None:
        chunks = db.get_chunks(document_id)
        entry = (BM25Index([c["text"] for c in chunks]), chunks)
        _cache[document_id] = entry
    return entry


def invalidate(document_id):
    _cache.pop(document_id, None)


def search_document(document_id, query, top_k=5):
    """Returns [{"page", "text", "score"}] for the best matching chunks."""
    index, chunks = _index_for(document_id)
    hits = index.search(query, top_k)
    return [
        {"page": chunks[i]["page"], "text": chunks[i]["text"], "score": round(score, 3)}
        for i, score in hits
    ]


def get_all_chunks(document_id):
    _, chunks = _index_for(document_id)
    return chunks
