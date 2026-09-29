export default function AgentToggle({ enabled, onChange }) {
  return (
    <div className="mx-4 mt-4 flex items-center justify-between rounded-lg border border-slate-800 bg-slate-900 px-3 py-3">
      <div>
        <p className="text-sm font-medium text-slate-200">Agent mode</p>
        <p className="text-xs text-slate-500">
          {enabled ? "Plans, searches PDF and web, self-checks" : "Answers from the PDF only"}
        </p>
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={enabled}
        onClick={() => onChange(!enabled)}
        className={`relative h-6 w-11 shrink-0 rounded-full transition ${
          enabled ? "bg-amber-400" : "bg-slate-700"
        }`}
      >
        <span
          className={`absolute top-0.5 h-5 w-5 rounded-full bg-slate-950 transition-all ${
            enabled ? "left-[22px]" : "left-0.5"
          }`}
        />
      </button>
    </div>
  );
}
