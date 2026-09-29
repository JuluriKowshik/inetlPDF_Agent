import { useEffect, useRef, useState } from "react";
import { listDocuments, sendChat, streamAgentChat } from "./api.js";
import AgentToggle from "./components/AgentToggle.jsx";
import ChatWindow from "./components/ChatWindow.jsx";
import UploadZone from "./components/UploadZone.jsx";

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [activeDocId, setActiveDocId] = useState(null);
  const [agentMode, setAgentMode] = useState(true);
  const [messages, setMessages] = useState([]);
  const [status, setStatus] = useState(null);
  const [busy, setBusy] = useState(false);
  const chatIdRef = useRef(null);

  useEffect(() => {
    listDocuments()
      .then((docs) => {
        setDocuments(docs);
        if (docs.length > 0) setActiveDocId(docs[0].id);
      })
      .catch(() => {});
  }, []);

  function handleUploaded(doc) {
    setDocuments((prev) => [
      { id: doc.document_id, filename: doc.filename, pages: doc.pages, chunk_count: doc.chunks },
      ...prev,
    ]);
    setActiveDocId(doc.document_id);
  }

  function newChat() {
    chatIdRef.current = null;
    setMessages([]);
    setStatus(null);
  }

  async function handleSend(question) {
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setBusy(true);
    setStatus(agentMode ? "planning" : "generating");
    try {
      if (agentMode) {
        await streamAgentChat(
          { question, documentId: activeDocId, chatId: chatIdRef.current },
          (event) => {
            if (event.type === "status" && event.status !== "done") {
              setStatus(event.status);
            } else if (event.type === "final") {
              chatIdRef.current = event.chat_id;
              setMessages((prev) => [
                ...prev,
                { role: "assistant", content: event.answer, meta: event },
              ]);
            } else if (event.type === "error") {
              setMessages((prev) => [
                ...prev,
                { role: "assistant", content: event.message, meta: { error: true } },
              ]);
            }
          }
        );
      } else {
        const data = await sendChat({
          question,
          documentId: activeDocId,
          chatId: chatIdRef.current,
        });
        chatIdRef.current = data.chat_id;
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: data.answer, meta: data },
        ]);
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: error.message, meta: { error: true } },
      ]);
    } finally {
      setBusy(false);
      setStatus(null);
    }
  }

  const activeDoc = documents.find((d) => d.id === activeDocId) || null;

  return (
    <div className="flex h-screen bg-slate-950 text-slate-200">
      <aside className="flex w-80 shrink-0 flex-col border-r border-slate-800 bg-slate-900/50">
        <div className="border-b border-slate-800 px-4 py-4">
          <h1 className="text-base font-semibold text-slate-100">IntelliPDF AI</h1>
          <p className="font-mono text-[11px] uppercase tracking-[0.25em] text-amber-400">
            Agent v2
          </p>
        </div>

        <UploadZone onUploaded={handleUploaded} />

        <div className="mt-4 flex-1 overflow-y-auto px-4">
          <p className="mb-2 font-mono text-[11px] uppercase tracking-wider text-slate-500">
            Documents
          </p>
          {documents.length === 0 && (
            <p className="text-xs text-slate-600">
              No documents yet. Upload a PDF, or ask a web question in Agent mode.
            </p>
          )}
          <div className="space-y-1.5">
            {documents.map((doc) => (
              <button
                key={doc.id}
                onClick={() => setActiveDocId(doc.id)}
                className={`w-full rounded-lg border px-3 py-2 text-left transition ${
                  doc.id === activeDocId
                    ? "border-amber-400/50 bg-amber-400/10"
                    : "border-slate-800 bg-slate-900 hover:border-slate-700"
                }`}
              >
                <p className="truncate text-sm text-slate-200">{doc.filename}</p>
                <p className="font-mono text-[11px] text-slate-500">{doc.pages} pages</p>
              </button>
            ))}
          </div>
        </div>

        <AgentToggle enabled={agentMode} onChange={setAgentMode} />

        <div className="px-4 py-4">
          <button
            onClick={newChat}
            className="w-full rounded-lg border border-slate-800 px-3 py-2 text-sm text-slate-400 transition hover:border-slate-600 hover:text-slate-200"
          >
            Start new chat
          </button>
        </div>
      </aside>

      <main className="flex min-w-0 flex-1 flex-col">
        <ChatWindow
          messages={messages}
          status={status}
          busy={busy}
          onSend={handleSend}
          agentMode={agentMode}
          activeDoc={activeDoc}
        />
      </main>
    </div>
  );
}
