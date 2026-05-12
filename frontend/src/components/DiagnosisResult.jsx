function severityStyles(sev) {
  const key = String(sev || "").toLowerCase();
  if (key === "high") return "border-rose-500/50 bg-rose-950/40 text-rose-100";
  if (key === "low") return "border-emerald-500/40 bg-emerald-950/35 text-emerald-100";
  return "border-amber-500/45 bg-amber-950/35 text-amber-100";
}

export default function DiagnosisResult({ diagnosis }) {
  if (!diagnosis) {
    return (
      <section className="flex h-full min-h-[320px] flex-col justify-center rounded-2xl border border-dashed border-white/15 bg-garage-900/40 p-8 text-center shadow-inner">
        <p className="font-display text-lg font-medium text-zinc-200">Awaiting case file</p>
        <p className="mt-2 text-sm text-zinc-500">
          Submit a new intake or choose a record from history to view ranked causes, cost band, and safety notes.
        </p>
      </section>
    );
  }

  const ai = diagnosis.ai_result || {};
  const causes = Array.isArray(ai.causes) ? ai.causes : [];

  return (
    <section className="rounded-2xl border border-white/10 bg-garage-900/70 p-6 shadow-panel backdrop-blur">
      <div className="flex flex-col gap-4 border-b border-white/10 pb-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-500">Active case</p>
          <h2 className="font-display text-2xl font-semibold text-white">
            {diagnosis.vehicle_year} {diagnosis.make} {diagnosis.model}
          </h2>
          {diagnosis.engine && <p className="text-sm text-zinc-400">{diagnosis.engine}</p>}
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge text={`Severity: ${ai.severity || "—"}`} className={severityStyles(ai.severity)} />
          <Badge
            text={ai.safe_to_drive ? "Safe to drive: Yes" : "Safe to drive: No"}
            className={
              ai.safe_to_drive
                ? "border-emerald-500/40 bg-emerald-950/35 text-emerald-100"
                : "border-rose-500/50 bg-rose-950/40 text-rose-100"
            }
          />
        </div>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <Meta label="Mileage" value={diagnosis.mileage != null ? `${Number(diagnosis.mileage).toLocaleString()} mi` : "—"} />
        <Meta label="OBD codes" value={diagnosis.obd_codes || "—"} mono />
        <Meta label="Symptoms" value={diagnosis.symptoms || "—"} className="sm:col-span-2" />
        <Meta label="Noise" value={diagnosis.noise_description || "—"} />
        <Meta label="Smell" value={diagnosis.smell_description || "—"} />
      </div>

      <div className="mt-5 rounded-xl border border-white/10 bg-black/35 p-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">Estimated repair cost</p>
        <p className="mt-1 font-display text-xl text-white">{ai.estimated_repair_cost_range || "—"}</p>
        <p className="mt-3 text-sm leading-relaxed text-zinc-300">{ai.summary}</p>
      </div>

      <div className="mt-6 space-y-4">
        <p className="text-xs font-semibold uppercase tracking-[0.25em] text-zinc-500">Top likely causes</p>
        {causes.length === 0 && <p className="text-sm text-zinc-500">No structured causes returned.</p>}
        {causes.map((c, idx) => (
          <article
            key={`${c.title}-${idx}`}
            className="rounded-xl border border-white/10 bg-gradient-to-br from-white/[0.03] to-transparent p-4"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs text-zinc-500">Rank {idx + 1}</p>
                <h3 className="font-medium text-zinc-100">{c.title}</h3>
              </div>
              <span className="rounded-full border border-white/10 bg-black/40 px-2.5 py-1 text-xs font-semibold text-accent">
                {Number(c.probability) || 0}%
              </span>
            </div>
            <div className="mt-3 h-2 overflow-hidden rounded-full bg-zinc-800">
              <div
                className="h-full rounded-full bg-gradient-to-r from-amber-600 via-amber-400 to-yellow-200"
                style={{ width: `${Math.min(100, Math.max(4, Number(c.probability) || 0))}%` }}
              />
            </div>
            <p className="mt-3 text-sm leading-relaxed text-zinc-300">{c.explanation}</p>
            <div className="mt-3 rounded-lg border border-sky-500/25 bg-sky-950/30 px-3 py-2 text-sm text-sky-100">
              <span className="font-semibold text-sky-200">Next steps: </span>
              {c.recommended_next_steps}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function Badge({ text, className }) {
  return <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${className}`}>{text}</span>;
}

function Meta({ label, value, mono, className = "" }) {
  return (
    <div className={`rounded-lg border border-white/5 bg-black/30 px-3 py-2 ${className}`}>
      <p className="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">{label}</p>
      <p className={`mt-1 text-sm text-zinc-200 ${mono ? "font-mono text-xs" : ""}`}>{value}</p>
    </div>
  );
}
