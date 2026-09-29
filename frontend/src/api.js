// API client. In dev, Vite proxies /api to the backend on port 8000.
// In production builds, set VITE_API_URL to the deployed backend URL.
const BASE = (import.meta.env && import.meta.env.VITE_API_URL) || "/api";

async function handle(res) {
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const data = await res.json();
      if (data.detail) detail = data.detail;
    } catch {
      // keep the default message
    }
    throw new Error(detail);
  }
  return res.json();
}

export function listDocuments() {
  return fetch(`${BASE}/documents`).then(handle);
}

export function uploadPdf(file) {
  const form = new FormData();
  form.append("file", file);
  return fetch(`${BASE}/upload`, { method: "POST", body: form }).then(handle);
}

export function sendChat({ question, documentId, chatId }) {
  return fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, document_id: documentId, chat_id: chatId }),
  }).then(handle);
}

// Reads the SSE stream from /agent/chat and calls onEvent for every
// parsed event: {type: "status"|"final"|"error", ...}
export async function streamAgentChat({ question, documentId, chatId }, onEvent) {
  const res = await fetch(`${BASE}/agent/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, document_id: documentId, chat_id: chatId }),
  });
  if (!res.ok || !res.body) {
    let detail = `Agent request failed (${res.status})`;
    try {
      const data = await res.json();
      if (data.detail) detail = data.detail;
    } catch {
      // keep the default message
    }
    throw new Error(detail);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop();
    for (const block of blocks) {
      for (const line of block.split("\n")) {
        if (line.startsWith("data: ")) {
          try {
            onEvent(JSON.parse(line.slice(6)));
          } catch {
            // skip malformed frame
          }
        }
      }
    }
  }
}
