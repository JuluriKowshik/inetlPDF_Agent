import { renderMarkdownLite } from "../markdown.js";
import RouteBadge from "./RouteBadge.jsx";
import Sources from "./Sources.jsx";

export default function MessageBubble({ message }) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[75%] whitespace-pre-wrap rounded-2xl rounded-br-sm bg-amber-400/90 px-4 py-2.5 text-sm text-slate-950">
          {message.content}
        </div>
      </div>
    );
  }

  const meta = message.meta || {};
  return (
    <div className="flex justify-start">
      <div
        className={`max-w-[85%] rounded-2xl rounded-bl-sm border px-4 py-3 text-sm leading-relaxed ${
          meta.error
            ? "border-rose-500/40 bg-rose-500/10 text-rose-200"
            : "border-slate-800 bg-slate-900 text-slate-200"
        }`}
      >
        {meta.route && (
          <div className="mb-2 flex items-center gap-2">
            <RouteBadge route={meta.route} />
            {meta.reflections > 1 && (
              <span className="font-mono text-[10px] text-slate-500">
                self-checked x{meta.reflections}
              </span>
            )}
          </div>
        )}
        <div dangerouslySetInnerHTML={{ __html: renderMarkdownLite(message.content) }} />
        <Sources sources={meta.sources} />
      </div>
    </div>
  );
}
