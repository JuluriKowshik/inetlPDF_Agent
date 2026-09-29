export default function Sources({ sources }) {
  if (!sources || sources.length === 0) return null;
  return (
    <div className="mt-3 flex flex-wrap gap-1.5 border-t border-slate-800 pt-2">
      {sources.map((source, i) =>
        source.type === "web" ? (
          <a
            key={i}
            href={source.url}
            target="_blank"
            rel="noreferrer"
            title={source.url}
            className="max-w-[240px] truncate rounded border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 font-mono text-[11px] text-emerald-300 hover:bg-emerald-500/20"
          >
            {source.title || source.url}
          </a>
        ) : (
          <span
            key={i}
            className="rounded border border-amber-400/30 bg-amber-400/10 px-2 py-0.5 font-mono text-[11px] text-amber-300"
          >
            {source.label || `p. ${source.page}`}
          </span>
        )
      )}
    </div>
  );
}
