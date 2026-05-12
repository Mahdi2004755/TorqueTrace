function preview(text, max = 120) {
  if (!text) return "—";
  const t = String(text).trim();
  return t.length > max ? `${t.slice(0, max)}…` : t;
}

export default function DiagnosisCard({ diagnosis, active, onSelect, onDelete }) {
  const ai = diagnosis.ai_result || {};
  const sev = String(ai.severity || "").toLowerCase();
  const sevClass =
    sev === "high"
      ? "text-rose-300 border-rose-500/40 bg-rose-950/30"
      : sev === "low"
        ? "text-emerald-300 border-emerald-500/35 bg-emerald-950/25"
        : "text-amber-200 border-amber-500/35 bg-amber-950/25";

  return (
    <article
      className={`group flex flex-col rounded-xl border bg-black/30 p-4 transition hover:border-accent/50 ${
        active ? "border-accent/70 shadow-[0_0_0_1px_rgba(245,158,11,0.35)]" : "border-white/10"
      }`}
    >
      <button type="button" onClick={onSelect} className="text-left">
        <div className="flex items-start justify-between gap-2">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">#{diagnosis.id}</p>
            <h3 className="font-display text-lg font-semibold text-white">
              {diagnosis.vehicle_year} {diagnosis.make} {diagnosis.model}
            </h3>
          </div>
          <span className={`rounded-full border px-2 py-0.5 text-[11px] font-semibold ${sevClass}`}>
            {ai.severity || "—"}
          </span>
        </div>
        <p className="mt-2 font-mono text-xs text-zinc-400">{diagnosis.obd_codes || "No codes logged"}</p>
        <p className="mt-2 text-sm text-zinc-400">{preview(diagnosis.symptoms)}</p>
        <p className="mt-3 text-xs text-zinc-500">
          {diagnosis.created_at ? new Date(diagnosis.created_at).toLocaleString() : ""}
        </p>
      </button>

      <div className="mt-4 flex items-center justify-between border-t border-white/5 pt-3">
        <p className="text-xs text-zinc-500">Top cause</p>
        <p className="max-w-[65%] truncate text-right text-xs font-medium text-zinc-200">
          {ai.causes?.[0]?.title || "—"}
        </p>
      </div>

      <div className="mt-3 flex gap-2">
        <button
          type="button"
          onClick={onSelect}
          className="flex-1 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs font-semibold text-zinc-100 transition hover:border-accent/60 hover:text-accent"
        >
          Open in panel
        </button>
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          className="rounded-lg border border-rose-500/30 bg-rose-950/30 px-3 py-2 text-xs font-semibold text-rose-200 transition hover:border-rose-400/70"
        >
          Delete
        </button>
      </div>
    </article>
  );
}
