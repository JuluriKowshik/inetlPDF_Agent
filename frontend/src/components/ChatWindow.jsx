import { useEffect, useRef, useState } from "react";
import MessageBubble from "./MessageBubble.jsx";
import StatusLine from "./StatusLine.jsx";

export default function ChatWindow({ messages, status, busy, onSend, agentMode, activeDoc }) {
  const [draft, setDraft] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, status]);

  function submit() {
    const question = draft.trim();
    if (!question || busy) return;
    setDraft("");
    onSend(question);
  }

  return (
    <>
      <header className="flex items-center justify-between border-b border-slate-800 px-6 py-3">
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-slate-200">
            {activeDoc ? activeDoc.filename : "No document selected"}
          </p>
          <p className="font-mono text-[11px] text-slate-500">
            {activeDoc
              ? `${activeDoc.pages} pages indexed`
              : agentMode
                ? "Agent mode can still answer web questions"
                : "Upload a PDF to use classic chat"}
          </p>
        </div>
        <span
          className={`shrink-0 rounded-full border px-2.5 py-1 font-mono text-[11px] ${
            agentMode
              ? "border-amber-400/40 bg-amber-400/10 text-amber-300"
              : "border-slate-700 text-slate-400"
          }`}
        >
          {agentMode ? "AGENT" : "CLASSIC RAG"}
        </span>
      </header>

      <div className="flex-1 space-y-4 overflow-y-auto px-6 py-5">
        {messages.length === 0 && (
          <div className="mx-auto mt-16 max-w-md text-center">
            <p className="font-mono text-xs uppercase tracking-[0.3em] text-amber-400/80">
              Ask anything
            </p>
            <p className="mt-3 text-sm text-slate-400">
              The agent decides per question: search the PDF, search the web, use both,
              summarize the whole document, or ask you to clarify.
            </p>
            <div className="mt-5 space-y-1.5 text-left font-mono text-xs text-slate-500">
              <p>&gt; What is the leave policy?</p>
              <p>&gt; Is this leave policy similar to Microsoft's?</p>
              <p>&gt; Summarize the entire document</p>
              <p>&gt; Who is Narendra Modi?</p>
            </div>
          </div>
        )}
        {messages.map((message, i) => (
          <MessageBubble key={i} message={message} />
        ))}
        {busy && <StatusLine status={status} />}
        <div ref={bottomRef} />
      </div>

      <div className="border-t border-slate-800 px-6 py-4">
        <div className="flex items-end gap-2 rounded-xl border border-slate-800 bg-slate-900 px-3 py-2 focus-within:border-amber-400/50">
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submit();
              }
            }}
            rows={1}
            placeholder={agentMode ? "Ask the agent anything..." : "Ask about the selected PDF..."}
            className="max-h-40 flex-1 resize-none bg-transparent text-sm text-slate-200 placeholder:text-slate-600 focus:outline-none"
          />
          <button
            onClick={submit}
            disabled={busy || !draft.trim()}
            className="rounded-lg bg-amber-400 px-4 py-1.5 text-sm font-medium text-slate-950 transition hover:bg-amber-300 disabled:opacity-40"
          >
            Send
          </button>
        </div>
      </div>
    </>
  );
}
