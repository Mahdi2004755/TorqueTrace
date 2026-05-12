const base = () => (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");

async function parseJson(res) {
  const text = await res.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export async function fetchAppConfig() {
  const res = await fetch(`${base()}/api/config`);
  if (!res.ok) throw new Error("Failed to load app config");
  return res.json();
}

export async function fetchDiagnoses() {
  const res = await fetch(`${base()}/api/diagnoses`);
  if (!res.ok) throw new Error("Failed to load diagnoses");
  return res.json();
}

export async function fetchDiagnosis(id) {
  const res = await fetch(`${base()}/api/diagnoses/${id}`);
  if (!res.ok) throw new Error("Failed to load diagnosis");
  return res.json();
}

export async function createDiagnosis(payload) {
  const res = await fetch(`${base()}/api/diagnose`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await parseJson(res);
  if (!res.ok) {
    const detail = typeof data === "object" && data?.detail ? JSON.stringify(data.detail) : String(data);
    throw new Error(detail || "Diagnosis request failed");
  }
  return data;
}

export async function deleteDiagnosis(id) {
  const res = await fetch(`${base()}/api/diagnoses/${id}`, { method: "DELETE" });
  if (!res.ok && res.status !== 204) throw new Error("Delete failed");
}
