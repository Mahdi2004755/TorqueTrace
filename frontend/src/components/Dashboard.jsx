import { useCallback, useEffect, useState } from "react";
import { createDiagnosis, deleteDiagnosis, fetchAppConfig, fetchDiagnoses } from "../lib/api.js";
import DiagnosisForm from "./DiagnosisForm.jsx";
import DiagnosisHistory from "./DiagnosisHistory.jsx";
import DiagnosisResult from "./DiagnosisResult.jsx";

const emptyForm = {
  vehicle_year: new Date().getFullYear() - 5,
  make: "",
  model: "",
  engine: "",
  mileage: "",
  symptoms: "",
  obd_codes: "",
  noise_description: "",
  smell_description: "",
};

export default function Dashboard() {
  const [items, setItems] = useState([]);
  const [loadingList, setLoadingList] = useState(true);
  const [listError, setListError] = useState("");
  const [active, setActive] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [appConfig, setAppConfig] = useState({
    openai_configured: false,
    torque_use_openai: false,
    llm_diagnostics_active: false,
    web_search_enabled_default: true,
  });

  const load = useCallback(async () => {
    setLoadingList(true);
    setListError("");
    try {
      const data = await fetchDiagnoses();
      setItems(data);
      setActive((current) => {
        if (!current) return data[0] || null;
        const still = data.find((d) => d.id === current.id);
        return still || data[0] || null;
      });
    } catch (e) {
      setListError(e.message || "Could not load history");
    } finally {
      setLoadingList(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    fetchAppConfig()
      .then(setAppConfig)
      .catch(() =>
        setAppConfig({
          openai_configured: false,
          torque_use_openai: false,
          llm_diagnostics_active: false,
          web_search_enabled_default: true,
        })
      );
  }, []);

  const handleSubmit = async (form) => {
    setSubmitting(true);
    setSubmitError("");
    try {
      const payload = {
        ...form,
        mileage: form.mileage === "" || form.mileage == null ? null : Number(form.mileage),
      };
      const created = await createDiagnosis(payload);
      setItems((prev) => [created, ...prev]);
      setActive(created);
    } catch (e) {
      setSubmitError(e.message || "Submit failed");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    await deleteDiagnosis(id);
    setItems((prev) => prev.filter((d) => d.id !== id));
    setActive((cur) => (cur?.id === id ? null : cur));
    await load();
  };

  return (
    <div className="min-h-screen pb-16">
      <header className="border-b border-white/10 bg-garage-900/60 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-6 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.25em] text-accent/90">Workshop console</p>
            <h1 className="font-display text-3xl font-semibold tracking-tight text-white sm:text-4xl">TorqueTrace</h1>
            <p className="mt-2 max-w-xl text-sm text-zinc-400">
              Symptom capture, OBD intelligence, and ranked repair guidance — tuned for a professional diagnostic bay.
            </p>
          </div>
          <div className="flex items-center gap-3 rounded-xl border border-white/10 bg-black/30 px-4 py-3 shadow-panel">
            <div className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_12px_rgba(52,211,153,0.9)]" />
            <div>
              <p className="text-xs text-zinc-500">System</p>
              <p className="text-sm font-medium text-zinc-200">Live diagnostics</p>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl space-y-8 px-4 pt-8 sm:px-6 lg:px-8">
        {!appConfig.llm_diagnostics_active && (
          <div className="rounded-xl border border-white/10 bg-zinc-900/50 px-4 py-3 text-sm text-zinc-400">
            <strong className="font-medium text-zinc-300">Offline diagnostics.</strong> The built-in rule engine is
            active — OpenAI is not called unless you set{" "}
            <code className="rounded bg-black/40 px-1.5 py-0.5 font-mono text-xs text-zinc-300">TORQUE_USE_OPENAI=true</code>{" "}
            and <code className="rounded bg-black/40 px-1.5 py-0.5 font-mono text-xs text-zinc-300">OPENAI_API_KEY</code>{" "}
            in <code className="rounded bg-black/40 px-1.5 py-0.5 font-mono text-xs text-zinc-300">backend/.env</code>, then
            restart the API.
          </div>
        )}

        {listError && (
          <div className="rounded-lg border border-rose-500/40 bg-rose-950/40 px-4 py-3 text-sm text-rose-100">
            {listError}
          </div>
        )}

        <div className="grid gap-8 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)]">
          <div className="space-y-6">
            <DiagnosisForm
              initialValues={emptyForm}
              onSubmit={handleSubmit}
              submitting={submitting}
              error={submitError}
            />
          </div>
          <div className="space-y-6">
            <DiagnosisResult diagnosis={active} />
          </div>
        </div>

        <DiagnosisHistory
          items={items}
          loading={loadingList}
          activeId={active?.id}
          onSelect={setActive}
          onDelete={handleDelete}
        />
      </main>
    </div>
  );
}
