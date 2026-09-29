const LABELS = {
  planning: "Planning",
  searching_pdf: "Searching PDF",
  searching_web: "Searching web",
  summarizing: "Summarizing document",
  generating: "Generating answer",
  reflecting: "Checking the answer",
};

export default function StatusLine({ status }) {
  if (!status) return null;
  return (
    <div className="flex items-center gap-2 px-1 py-2 font-mono text-xs text-amber-300">
      <span className="h-2 w-2 animate-pulse rounded-full bg-amber-400" />
      {LABELS[status] || status}...
    </div>
  );
}
