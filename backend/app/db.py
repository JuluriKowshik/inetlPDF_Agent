"""SQLite storage: documents, chunks, chats, messages."""
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "intellipdf.db"


def _now():
    return datetime.now(timezone.utc).isoformat()


def get_conn():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents(
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                pages INTEGER NOT NULL,
                chunk_count INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS chunks(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                page INTEGER NOT NULL,
                text TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(document_id);
            CREATE TABLE IF NOT EXISTS chats(
                id TEXT PRIMARY KEY,
                document_id TEXT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                meta TEXT,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_messages_chat ON messages(chat_id);
            """
        )


def save_document(filename, pages, chunks):
    """chunks: list of {"page": int, "text": str}. Returns the new document id."""
    doc_id = uuid.uuid4().hex
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO documents(id, filename, pages, chunk_count, created_at) VALUES(?,?,?,?,?)",
            (doc_id, filename, pages, len(chunks), _now()),
        )
        conn.executemany(
            "INSERT INTO chunks(document_id, page, text) VALUES(?,?,?)",
            [(doc_id, c["page"], c["text"]) for c in chunks],
        )
    return doc_id


def get_document(doc_id):
    if not doc_id:
        return None
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM documents WHERE id=?", (doc_id,)).fetchone()
    return dict(row) if row else None


def list_documents():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM documents ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


def get_chunks(doc_id):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT page, text FROM chunks WHERE document_id=? ORDER BY id", (doc_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def ensure_chat(chat_id, document_id):
    """Returns a valid chat id, creating the chat row if needed."""
    if not chat_id:
        chat_id = uuid.uuid4().hex
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO chats(id, document_id, created_at) VALUES(?,?,?)",
            (chat_id, document_id, _now()),
        )
    return chat_id


def add_message(chat_id, role, content, meta=None):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO messages(chat_id, role, content, meta, created_at) VALUES(?,?,?,?,?)",
            (chat_id, role, content, json.dumps(meta) if meta else None, _now()),
        )


def get_recent_messages(chat_id, limit=6):
    """Last `limit` messages in chronological order, as [{"role","content"}]."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE chat_id=? ORDER BY id DESC LIMIT ?",
            (chat_id, limit),
        ).fetchall()
    return [dict(r) for r in reversed(rows)]
