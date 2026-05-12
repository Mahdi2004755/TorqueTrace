import { useMemo, useState } from "react";

const samples = [
  {
    label: "P0420 + sulfur + rough idle",
    values: {
      vehicle_year: 2015,
      make: "Subaru",
      model: "Outback",
      engine: "2.5L H4",
      mileage: 134000,
      symptoms: "Check engine light, rough idle at stop lights",
      obd_codes: "P0420",
      noise_description: "",
      smell_description: "Sulfur smell after hard acceleration",
    },
  },
  {
    label: "P0430 + P0300 + ticking",
    values: {
      vehicle_year: 2013,
      make: "Chevrolet",
      model: "Silverado",
      engine: "5.3L V8",
      mileage: 178000,
      symptoms: "Shaking under load, power loss",
      obd_codes: "P0430, P0300",
      noise_description: "Fast ticking noise that follows RPM",
      smell_description: "",
    },
  },
  {
    label: "Overheating in traffic",
    values: {
      vehicle_year: 2010,
      make: "Nissan",
      model: "Altima",
      engine: "2.5L I4",
      mileage: 165000,
      symptoms: "Temperature rises in traffic, rough idle when hot",
      obd_codes: "",
      noise_description: "",
      smell_description: "",
    },
  },
];

export default function DiagnosisForm({ initialValues, onSubmit, submitting, error }) {
  const [form, setForm] = useState(initialValues);

  const canSubmit = useMemo(() => {
    return String(form.make || "").trim() && String(form.model || "").trim() && form.vehicle_year;
  }, [form]);

  const update = (key, value) => setForm((f) => ({ ...f, [key]: value }));

  const applySample = (sample) => {
    setForm((f) => ({
      ...f,
      ...sample.values,
      mileage: sample.values.mileage ?? "",
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!canSubmit) return;
    onSubmit(form);
  };

  return (
    <section className="rounded-2xl border border-white/10 bg-garage-900/70 p-6 shadow-panel backdrop-blur">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="font-display text-xl font-semibold text-white">New intake</h2>
          <p className="text-sm text-zinc-400">Vehicle context, codes, and sensory clues the model weighs together.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {samples.map((s) => (
            <button
              key={s.label}
              type="button"
              onClick={() => applySample(s)}
              className="rounded-full border border-white/10 bg-black/40 px-3 py-1 text-xs font-medium text-zinc-200 transition hover:border-accent/60 hover:text-accent"
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={handleSubmit} className="mt-6 grid gap-4 sm:grid-cols-2">
        <Field label="Year" required>
          <input
            type="number"
            className="input"
            value={form.vehicle_year}
            onChange={(e) => update("vehicle_year", Number(e.target.value))}
            min="1980"
            max="2035"
            required
          />
        </Field>
        <Field label="Mileage">
          <input
            type="number"
            className="input"
            value={form.mileage}
            onChange={(e) => update("mileage", e.target.value)}
            min="0"
            placeholder="e.g. 120000"
          />
        </Field>
        <Field label="Make" required>
          <input
            type="text"
            className="input"
            value={form.make}
            onChange={(e) => update("make", e.target.value)}
            placeholder="e.g. Ford"
            required
          />
        </Field>
        <Field label="Model" required>
          <input
            type="text"
            className="input"
            value={form.model}
            onChange={(e) => update("model", e.target.value)}
            placeholder="e.g. Mustang"
            required
          />
        </Field>
        <Field label="Engine" className="sm:col-span-2">
          <input
            type="text"
            className="input"
            value={form.engine}
            onChange={(e) => update("engine", e.target.value)}
            placeholder="e.g. 2.3L EcoBoost I4"
          />
        </Field>
        <Field label="Symptoms" className="sm:col-span-2">
          <textarea
            className="input min-h-[88px]"
            value={form.symptoms}
            onChange={(e) => update("symptoms", e.target.value)}
            placeholder="Rough idle, hesitation, smoke, overheating…"
          />
        </Field>
        <Field label="OBD-II codes" className="sm:col-span-2">
          <input
            type="text"
            className="input font-mono text-sm"
            value={form.obd_codes}
            onChange={(e) => update("obd_codes", e.target.value)}
            placeholder="P0420, P0300, P0430…"
          />
        </Field>
        <Field label="Noise description">
          <textarea
            className="input min-h-[80px]"
            value={form.noise_description}
            onChange={(e) => update("noise_description", e.target.value)}
            placeholder="Ticking, grinding, whine under load…"
          />
        </Field>
        <Field label="Smell description">
          <textarea
            className="input min-h-[80px]"
            value={form.smell_description}
            onChange={(e) => update("smell_description", e.target.value)}
            placeholder="Sulfur, sweet coolant, burning oil…"
          />
        </Field>

        {error && (
          <div className="sm:col-span-2 rounded-lg border border-rose-500/40 bg-rose-950/40 px-3 py-2 text-sm text-rose-100">
            {error}
          </div>
        )}

        <div className="sm:col-span-2 flex flex-wrap items-center justify-between gap-3 border-t border-white/10 pt-4">
          <p className="text-xs text-zinc-500">
            Outputs include ranked causes, severity, cost band, and drive-away safety guidance.
          </p>
          <button
            type="submit"
            disabled={!canSubmit || submitting}
            className="inline-flex items-center justify-center rounded-xl bg-accent px-5 py-2.5 text-sm font-semibold text-garage-950 shadow-lg shadow-amber-500/25 transition hover:bg-amber-400 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {submitting ? "Running analysis…" : "Run AI diagnosis"}
          </button>
        </div>
      </form>

      <style>{`
        .input {
          width: 100%;
          border-radius: 0.75rem;
          border: 1px solid rgba(255,255,255,0.08);
          background: rgba(0,0,0,0.35);
          padding: 0.65rem 0.85rem;
          font-size: 0.875rem;
          color: #f4f4f5;
          outline: none;
          transition: border-color 0.15s ease, box-shadow 0.15s ease;
        }
        .input:focus {
          border-color: rgba(245, 158, 11, 0.65);
          box-shadow: 0 0 0 1px rgba(245, 158, 11, 0.35);
        }
        .input::placeholder {
          color: #71717a;
        }
      `}</style>
    </section>
  );
}

function Field({ label, children, required, className = "" }) {
  return (
    <label className={`block text-sm ${className}`}>
      <span className="mb-1.5 flex items-center gap-1 text-xs font-semibold uppercase tracking-wide text-zinc-500">
        {label}
        {required && <span className="text-accent">*</span>}
      </span>
      {children}
    </label>
  );
}
