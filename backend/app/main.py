"""FastAPI routes: upload, documents, classic RAG chat, and the SSE agent chat."""
import json
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from . import config, db, llm, pdf, prompts, retrieval, websearch
from .agent.graph import agent_graph
from .agent.status import status_after

config.load_env()


@asynccontextmanager
async def lifespan(_app):
    db.init_db()
    yield


app = FastAPI(title="IntelliPDF AI Agent", version="2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str
    document_id: Optional[str] = None
    chat_id: Optional[str] = None


def _history_block(history):
    if not history:
        return ""
    lines = "\n".join(f"{m['role']}: {m['content']}" for m in history)
    return f"Recent conversation:\n{lines}\n\n"


def _sse(payload):
    return f"data: {json.dumps(payload)}\n\n"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    data = await file.read()
    try:
        pages = pdf.extract_pages(data)
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read this file as a PDF.")
    chunks = pdf.chunk_pages(pages)
    if not chunks:
        raise HTTPException(
            status_code=400,
            detail="No extractable text found. Scanned PDFs need OCR, which is not part of this version.",
        )
    doc_id = db.save_document(file.filename, len(pages), chunks)
    retrieval.invalidate(doc_id)
    return {
        "document_id": doc_id,
        "filename": file.filename,
        "pages": len(pages),
        "chunks": len(chunks),
    }


@app.get("/documents")
def documents():
    return db.list_documents()


@app.post("/chat")
def classic_chat(req: ChatRequest):
    """Classic RAG over the selected PDF. Unchanged behavior, no agent."""
    if not req.document_id or not db.get_document(req.document_id):
        raise HTTPException(
            status_code=400,
            detail="Select an uploaded document first. Classic chat answers from the PDF only.",
        )
    chat_id = db.ensure_chat(req.chat_id, req.document_id)
    history = db.get_recent_messages(chat_id)
    hits = retrieval.search_document(req.document_id, req.question)
    context = "\n\n".join(f"[p. {c['page']}] {c['text']}" for c in hits)
    if not context:
        context = "(no matching passages found)"
    try:
        answer = llm.chat(
            [
                {"role": "system", "content": prompts.CLASSIC_SYSTEM},
                {
                    "role": "user",
                    "content": prompts.GENERATE_USER.format(
                        history_block=_history_block(history),
                        question=req.question,
                        context="Document context:\n" + context,
                    ),
                },
            ]
        )
    except llm.LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    sources, seen = [], set()
    for hit in hits:
        if hit["page"] not in seen:
            seen.add(hit["page"])
            sources.append({"type": "pdf", "page": hit["page"]})
    db.add_message(chat_id, "user", req.question)
    db.add_message(chat_id, "assistant", answer, {"route": "PDF", "sources": sources})
    return {"answer": answer, "sources": sources, "chat_id": chat_id, "route": "PDF"}


@app.post("/agent/chat")
def agent_chat(req: ChatRequest):
    """Runs the LangGraph agent and streams status events over SSE."""
    document = db.get_document(req.document_id) if req.document_id else None
    chat_id = db.ensure_chat(req.chat_id, document["id"] if document else None)
    history = db.get_recent_messages(chat_id)
    state = {
        "question": req.question,
        "chat_history": history,
        "document_id": document["id"] if document else None,
        "has_document": document is not None,
    }

    def stream():
        yield _sse({"type": "status", "status": "planning"})
        final = dict(state)
        try:
            for update in agent_graph.stream(state, stream_mode="updates"):
                for node, delta in update.items():
                    if isinstance(delta, dict):
                        final.update(delta)
                    status = status_after(node, final)
                    if status:
                        yield _sse({"type": "status", "status": status})
        except (llm.LLMError, websearch.WebSearchError) as exc:
            yield _sse({"type": "error", "message": str(exc)})
            return
        except Exception as exc:  # keep the stream well-formed on any failure
            yield _sse({"type": "error", "message": f"Agent failed: {exc}"})
            return

        payload = {
            "type": "final",
            "answer": final.get("answer", ""),
            "route": final.get("route", ""),
            "sources": final.get("sources", []),
            "reflections": final.get("reflections", 0),
            "clarify": bool(final.get("clarify")),
            "chat_id": chat_id,
        }
        db.add_message(chat_id, "user", req.question)
        db.add_message(
            chat_id,
            "assistant",
            payload["answer"],
            {
                "route": payload["route"],
                "sources": payload["sources"],
                "reflections": payload["reflections"],
                "clarify": payload["clarify"],
            },
        )
        yield _sse(payload)
        yield _sse({"type": "status", "status": "done"})

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
