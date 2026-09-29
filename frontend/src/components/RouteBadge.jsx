const STYLES = {
  PDF: "bg-sky-500/15 text-sky-300 border-sky-500/30",
  WEB: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  BOTH: "bg-violet-500/15 text-violet-300 border-violet-500/30",
  SUMMARY: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  CLARIFY: "bg-rose-500/15 text-rose-300 border-rose-500/30",
};

const LABELS = {
  PDF: "PDF",
  WEB: "Web",
  BOTH: "PDF + Web",
  SUMMARY: "Summary",
  CLARIFY: "Clarify",
};

export default function RouteBadge({ route }) {
  if (!route || !STYLES[route]) return null;
  return (
    <span
      className={`inline-block rounded border px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider ${STYLES[route]}`}
    >
      {LABELS[route]}
    </span>
  );
}
