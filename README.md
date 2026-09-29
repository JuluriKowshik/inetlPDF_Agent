# IntelliPDF AI Agent (V2)

An AI Research Assistant that decides per question how to answer: search the uploaded PDF, search the web, combine both, summarize the whole document, or ask you to clarify. Built with FastAPI, SQLite, BM25, PyMuPDF, LangGraph, Groq, and Tavily on the backend, and React, Vite, and Tailwind CSS on the frontend.

Everything installs with pip and npm only. No system software, no Docker, no databases to install. It runs from VS Code on a locked-down laptop.

## How the agent decides

| Route | Example question | What happens |
|---|---|---|
| PDF | What is the leave policy? | BM25 search inside the uploaded PDF, answer with page citations like (p. 18) |
| BOTH | Is this leave policy similar to Microsoft's? | PDF search, then Tavily web search, one combined answer with page and URL citations |
| SUMMARY | Summarize the entire document | Reads all chunks in batches, no retrieval, returns one summary |
| WEB | Who is Narendra Modi? | Tavily web search only, answer with source URLs |
| CLARIFY | What about that thing? | Asks you one clarifying question instead of guessing |

After PDF, WEB, and BOTH answers, a reflection step checks whether the draft actually answers the question. If not, it refines the search query and retries. Hard cap: 2 reflection loops, then it returns the best draft.

The whole run streams live status events to the UI: planning, searching_pdf, searching_web, summarizing, generating, reflecting, done.

## Prerequisites

- Python 3.10 or newer
- Node.js 18 or newer
- A Groq API key (free): https://console.groq.com/keys
- A Tavily API key (free): https://app.tavily.com

## Setup

Run the backend and the frontend in two separate terminals.

### 1. Backend (terminal 1)

Windows (PowerShell):

```
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python run.py
```

macOS or Linux:

```
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python run.py
```

Open `backend/.env` and set your keys before asking questions:

```
GROQ_API_KEY=your_groq_key_here
GROQ_MODEL=openai/gpt-oss-20b
TAVILY_API_KEY=your_tavily_key_here
```

Then restart the backend. The API runs on http://127.0.0.1:8000

### 2. Frontend (terminal 2)

```
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Verifying the install

Upload any text PDF, keep Agent mode on, and ask these five questions. Each should show a different route badge:

1. What is the leave policy? (PDF badge, page citations)
2. Is this leave policy similar to Microsoft's? (PDF + Web badge, page and URL citations)
3. Summarize the entire document (Summary badge)
4. Who is Narendra Modi? (Web badge, URL citations)
5. What about that thing? (Clarify badge, asks you a question back)

The Agent mode toggle in the sidebar switches between the agent and classic RAG. Classic mode calls the old `/chat` endpoint, which is unchanged: BM25 over the selected PDF, one LLM call, no planner, no web, no reflection.

## Running the tests

```
cd backend
python -m pytest tests -q
```

The suite tests planner routing for all five scenarios with a mocked LLM, plus the fallback rules (bad JSON falls back to PDF when a document is loaded and WEB when not, and document routes are downgraded when no document exists).

## Project structure

```
backend/
  run.py                start the API server
  requirements.txt      Python dependencies
  .env.example          environment template
  app/
    main.py             FastAPI routes: /upload, /documents, /chat, /agent/chat (SSE)
    config.py           .env loader (standard library)
    db.py               SQLite schema and helpers
    pdf.py              PyMuPDF extraction and page-preserving chunking
    bm25.py             pure Python BM25 index
    retrieval.py        per-document index cache and search
    llm.py              Groq client with retry
    websearch.py        Tavily client
    prompts.py          all prompts
    agent/
      state.py          AgentState definition
      routing.py        planner and reflection output parsing with fallbacks
      nodes.py          plan, search_pdf, search_web, generate, reflect, summarize, clarify
      graph.py          LangGraph wiring
      status.py         node-to-status mapping for the SSE stream
  tests/
    test_planner.py     planner routing tests with a mocked LLM
frontend/
  src/
    App.jsx             layout, state, send flow
    api.js              API client and SSE stream reader
    markdown.js         markdown-lite renderer
    components/         UploadZone, AgentToggle, ChatWindow, MessageBubble,
                        RouteBadge, Sources, StatusLine
```

## How the streaming works

`POST /agent/chat` returns a server-sent event stream. Every frame is one line: `data: {json}`. Event types:

- `{"type": "status", "status": "planning" | "searching_pdf" | "searching_web" | "summarizing" | "generating" | "reflecting" | "done"}`
- `{"type": "final", "answer", "route", "sources", "reflections", "clarify", "chat_id"}`
- `{"type": "error", "message"}`

The backend iterates the LangGraph run with `stream_mode="updates"` and emits the next status after each node finishes, so what you see matches what the agent is actually doing, including retry loops.

## Deploying on Render (free tier)

Backend (web service):
- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Environment variables: `GROQ_API_KEY`, `GROQ_MODEL`, `TAVILY_API_KEY`

Frontend (static site):
- Root directory: `frontend`
- Build command: `npm install && npm run build`
- Publish directory: `dist`
- Environment variable: `VITE_API_URL` set to your backend URL, for example `https://your-backend.onrender.com`

Note: the free tier disk is ephemeral. Uploaded PDFs and the SQLite database are wiped when the service sleeps, same as V1. Keep the UptimeRobot ping, or move storage to Supabase later.

## Troubleshooting

- "GROQ_API_KEY is not set": edit `backend/.env` and restart the backend.
- "TAVILY_API_KEY is not set": same fix. Only WEB and BOTH routes need it.
- "No extractable text found": the PDF pages are pictures. OCR is not part of this version; use a text PDF.
- Frontend loads but requests fail: the backend is not running, or the port changed. The dev proxy targets http://127.0.0.1:8000 in `frontend/vite.config.js`.
- Port already in use: stop whatever runs on 8000 or 5173, or change the port in `backend/run.py` and the proxy target together.
- Groq error 400 about the model: the model in `GROQ_MODEL` may be decommissioned. Pick a current one from the Groq console and update `.env`.

## Security

Never commit `backend/.env`. It is in `.gitignore`. If an API key was ever pasted into a chat, a repo, or a screenshot, treat it as burned: delete it in the provider dashboard and create a new one.

## MVP boundary and next steps

Not included on purpose: multi-PDF questions, persistent conversation memory across restarts, confidence scores, automatic follow-up detection, and OCR for scanned PDFs. Natural next steps: Supabase storage for uploads, hybrid retrieval (BM25 plus vectors), and porting V1 features like page rendering with citation highlights.
