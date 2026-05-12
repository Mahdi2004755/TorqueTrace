import DiagnosisCard from "./DiagnosisCard.jsx";

export default function DiagnosisHistory({ items, loading, activeId, onSelect, onDelete }) {
  return (
    <section className="rounded-2xl border border-white/10 bg-garage-900/60 p-6 shadow-panel backdrop-blur">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="font-display text-xl font-semibold text-white">Case history</h2>
          <p className="text-sm text-zinc-500">Latest intakes stored in PostgreSQL for this workshop.</p>
        </div>
        {loading && <span className="text-xs text-zinc-500">Refreshing…</span>}
      </div>

      {!loading && items.length === 0 && (
        <p className="mt-6 text-sm text-zinc-500">No saved diagnoses yet — run an intake to populate the bay log.</p>
      )}

      <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {items.map((d) => (
          <DiagnosisCard
            key={d.id}
            diagnosis={d}
            active={d.id === activeId}
            onSelect={() => onSelect(d)}
            onDelete={() => onDelete(d.id)}
          />
        ))}
      </div>
    </section>
  );
}
