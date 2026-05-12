"""OpenAI-backed diagnosis with optional web search (Responses API) + synthesis; rule-based fallback."""

from __future__ import annotations

import json
import os
import re
from typing import Any

from openai import OpenAI

from schemas import DiagnoseRequest


def _normalize_codes(text: str | None) -> list[str]:
    if not text:
        return []
    found = re.findall(r"P\d{4}", text.upper().replace(" ", ""))
    return list(dict.fromkeys(found))


def _text_blob(req: DiagnoseRequest) -> str:
    parts = [
        req.symptoms or "",
        req.noise_description or "",
        req.smell_description or "",
        req.obd_codes or "",
    ]
    return " ".join(parts).lower()


def _truthy(val: str | None, default: bool = True) -> bool:
    if val is None or val.strip() == "":
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


RULE_OBD: dict[str, dict[str, Any]] = {
    "P0420": {
        "title": "Catalyst system efficiency below threshold (Bank 1)",
        "probability": 78,
        "explanation": "P0420 usually indicates the Bank 1 catalytic converter is not cleaning exhaust gases as expected. Common contributors include a failing cat, exhaust leaks upstream, bad O2 sensors, or engine misfires that poisoned the catalyst.",
        "next_steps": "Scan for additional codes, verify exhaust for leaks before the cat, graph O2 sensors, and confirm no misfires or rich/lean conditions. If the cat is confirmed bad, replacement is typical.",
    },
    "P0430": {
        "title": "Catalyst system efficiency below threshold (Bank 2)",
        "probability": 76,
        "explanation": "P0430 mirrors P0420 but for Bank 2. Causes are similar: degraded catalytic converter, faulty downstream O2 sensor interpretation, exhaust leaks, or upstream engine issues.",
        "next_steps": "Same diagnostic path as Bank 1: leak check, O2 behavior, misfuel/misfire history, and catalytic converter testing before replacing parts.",
    },
    "P0300": {
        "title": "Random / multiple cylinder misfire detected",
        "probability": 82,
        "explanation": "P0300 means misfires are occurring on more than one cylinder or randomly. Typical causes include ignition components (coils, plugs, wires), vacuum leaks, fuel delivery issues, or mechanical compression problems.",
        "next_steps": "Retrieve cylinder-specific misfire counts if available, inspect spark plugs and coils, check fuel trims and vacuum leaks, and run a compression/leak-down test if needed.",
    },
}

RULE_KEYWORDS: list[tuple[list[str], dict[str, Any]]] = [
    (
        ["rough idle", "idle rough", "shaking at idle", "idle surge"],
        {
            "title": "Idle air / vacuum leak or ignition-fuel imbalance",
            "probability": 68,
            "explanation": "Rough idle often traces to unmetered air (vacuum leak), dirty throttle body/IAC (if applicable), fouled plugs, weak coil, or fuel trim issues. Carboned intake valves can also cause uneven idle on some engines.",
            "next_steps": "Check live fuel trims at idle, smoke test for vacuum leaks, inspect plugs/coils, clean throttle body if indicated, and review recent maintenance.",
        },
    ),
    (
        ["sulfur", "rotten egg", "eggs", "cat smell"],
        {
            "title": "Rich running or catalytic converter odor (sulfur compounds)",
            "probability": 64,
            "explanation": "A sulfur or rotten-egg smell often appears when the engine runs rich or the catalytic converter is processing excess hydrogen sulfide. A failing cat can also produce unusual odors.",
            "next_steps": "Check fuel trims and O2 sensors, inspect for misfires, verify the EVAP system, and evaluate converter health especially if paired with P0420/P0430.",
        },
    ),
    (
        ["tick", "ticking", "lifter", "valve train"],
        {
            "title": "Valve train tick or accessory/component noise",
            "probability": 62,
            "explanation": "Ticking may be normal injector noise, exhaust leak tick, low oil level, or valvetrain wear. Some engines are sensitive to oil type/pressure and develop lifter noise when cold.",
            "next_steps": "Verify oil level and pressure, use a mechanic's stethoscope to isolate the source, check for exhaust manifold leaks, and compare noise hot vs cold.",
        },
    ),
    (
        ["overheat", "overheating", "running hot", "temperature gauge", "temperature high"],
        {
            "title": "Cooling system fault or head gasket breach",
            "probability": 74,
            "explanation": "Overheating is commonly caused by low coolant, stuck thermostat, failed water pump, clogged radiator, cooling fan issues, or combustion gases entering the coolant from a head gasket leak.",
            "next_steps": "Do not continue driving if temperature is high. After cool-down, check coolant level, fan operation, thermostat, and look for bubbles in the radiator/overflow at idle (sign of gasket issues).",
        },
    ),
]


def _rule_based_diagnosis(req: DiagnoseRequest) -> dict[str, Any]:
    codes = _normalize_codes(req.obd_codes)
    blob = _text_blob(req)

    candidates: list[dict[str, Any]] = []

    for code in codes:
        if code in RULE_OBD:
            row = RULE_OBD[code].copy()
            row["code"] = code
            candidates.append(row)

    for keywords, payload in RULE_KEYWORDS:
        if any(k in blob for k in keywords):
            candidates.append(payload.copy())

    if not candidates:
        candidates.append(
            {
                "title": "General drivability / maintenance-related issue",
                "probability": 45,
                "explanation": "No specific OBD code pattern matched the built-in rule library. Symptoms may still point to maintenance items (filters, fluids), minor sensor drift, or an intermittent fault not captured in the text.",
                "next_steps": "Perform a full OBD scan, review freeze-frame data, verify maintenance history, and consider a road test with live data logging.",
            }
        )

    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for c in candidates:
        t = c["title"]
        if t in seen:
            continue
        seen.add(t)
        unique.append(c)

    unique.sort(key=lambda x: x["probability"], reverse=True)
    top = unique[:3]

    while len(top) < 3:
        top.append(
            {
                "title": "Secondary diagnosis: verify with inspection and data",
                "probability": max(15, 40 - len(top) * 10),
                "explanation": "Additional possibilities often include wiring/connectors, ground issues, or module communication faults that require scan data and visual inspection.",
                "next_steps": "Document all modules and codes, perform a visual wiring inspection, and retest after verifying battery/charging health.",
            }
        )

    total = sum(c["probability"] for c in top) or 1
    raw_pcts = [int(round(100 * c["probability"] / total)) for c in top]
    s = sum(raw_pcts) or 1
    raw_pcts = [max(5, int(round(100 * p / s))) for p in raw_pcts]
    diff = 100 - sum(raw_pcts)
    if raw_pcts:
        raw_pcts[0] = max(5, raw_pcts[0] + diff)

    causes = []
    for c, pct in zip(top, raw_pcts):
        causes.append(
            {
                "title": c["title"],
                "probability": min(95, max(8, pct)),
                "explanation": c["explanation"],
                "recommended_next_steps": c["next_steps"],
            }
        )

    max_prob = max(x["probability"] for x in causes)
    if max_prob >= 75:
        severity = "High"
        cost = "$400 – $2,500+ (wide range until verified)"
        unsafe = (
            "overheat" in blob
            or "overheating" in blob
            or "smoke" in blob
            or "P0300" in (req.obd_codes or "").upper()
        )
        safe_to_drive = not unsafe
    elif max_prob >= 55:
        severity = "Medium"
        cost = "$150 – $900 (typical if sensors/maintenance)"
        safe_to_drive = "overheat" not in blob
    else:
        severity = "Low"
        cost = "$80 – $450"
        safe_to_drive = True

    if "overheat" in blob or "overheating" in blob:
        severity = "High"
        safe_to_drive = False

    summary = (
        f"Rule-based assessment for {req.vehicle_year} {req.make} {req.model}: "
        f"primary suspicion is {causes[0]['title'].lower()}. "
        "For deeper, vehicle-specific answers, set OPENAI_API_KEY to enable ChatGPT with optional web research."
    )

    return {
        "causes": causes[:3],
        "severity": severity,
        "estimated_repair_cost_range": cost,
        "safe_to_drive": safe_to_drive,
        "summary": summary,
        "used_web_search": False,
        "research_notes": None,
        "research_sources": [],
    }


def _research_models() -> list[str]:
    raw = os.getenv("OPENAI_RESEARCH_MODEL", "").strip()
    if raw:
        return [m.strip() for m in raw.split(",") if m.strip()]
    return ["gpt-4.1", "gpt-4o", "gpt-4o-mini"]


def _synthesis_model() -> str:
    return (os.getenv("OPENAI_MODEL", "gpt-4o").strip() or "gpt-4o")


def _build_research_prompt(req: DiagnoseRequest) -> str:
    return f"""You have access to web search. Use it to research this automotive workshop case and produce a concise technical memo.

Vehicle: {req.vehicle_year} {req.make} {req.model}
Engine: {req.engine or "not specified"}
Mileage: {req.mileage if req.mileage is not None else "not specified"}

Symptoms / complaint:
{req.symptoms or "(none)"}

OBD-II codes (if any):
{req.obd_codes or "(none)"}

Noise:
{req.noise_description or "(none)"}

Smell:
{req.smell_description or "(none)"}

Instructions:
1) Run targeted searches for the codes + vehicle family + symptoms (e.g., forums, TSB summaries, manufacturer service bulletins where available, reputable repair guides).
2) Summarize what each code typically implies for this era of vehicle (not generic only — tie to likely subsystems).
3) List the most plausible mechanical/electrical causes ranked by likelihood, with 1–2 sentences of evidence each.
4) Call out safety-critical differentials (overheating, brake loss, fuel leaks, exhaust leaks into cabin, runaway acceleration risk, etc.).
5) Recommend a sensible verification sequence (what to check first with minimal parts cost).

Write the memo in clear Markdown with short sections. Be explicit and practical."""


def _responses_text_and_sources(response: Any) -> tuple[str, list[dict[str, str]]]:
    text_parts: list[str] = []
    sources: list[dict[str, str]] = []
    seen: set[str] = set()

    ot = getattr(response, "output_text", None)
    if ot:
        text_parts.append(str(ot))

    output = getattr(response, "output", None)
    if output is None and isinstance(response, dict):
        output = response.get("output")

    if not output:
        return ("\n\n".join(text_parts).strip(), sources)

    for item in output:
        itype = getattr(item, "type", None)
        if itype is None and isinstance(item, dict):
            itype = item.get("type")
        if itype != "message":
            continue

        content = getattr(item, "content", None)
        if content is None and isinstance(item, dict):
            content = item.get("content") or []

        for block in content or []:
            btype = getattr(block, "type", None)
            if btype is None and isinstance(block, dict):
                btype = block.get("type")
            if btype not in ("output_text", "text"):
                continue

            t = getattr(block, "text", None)
            if t is None and isinstance(block, dict):
                t = block.get("text")
            if t:
                text_parts.append(str(t))

            annots = getattr(block, "annotations", None)
            if annots is None and isinstance(block, dict):
                annots = block.get("annotations") or []

            for ann in annots or []:
                atype = getattr(ann, "type", None)
                if atype is None and isinstance(ann, dict):
                    atype = ann.get("type")
                if atype != "url_citation":
                    continue
                url = getattr(ann, "url", None) or (ann.get("url") if isinstance(ann, dict) else None)
                title = getattr(ann, "title", None) or (ann.get("title") if isinstance(ann, dict) else "") or ""
                if url and str(url) not in seen:
                    seen.add(str(url))
                    sources.append({"url": str(url), "title": str(title) if title else str(url)})

    return ("\n\n".join(text_parts).strip(), sources)


def _web_research_memo(client: OpenAI, req: DiagnoseRequest) -> tuple[str, list[dict[str, str]], str | None]:
    prompt = _build_research_prompt(req)
    last_err: str | None = None

    for model in _research_models():
        for attempt in (1, 2):
            try:
                if attempt == 1:
                    resp = client.responses.create(
                        model=model,
                        input=prompt,
                        tools=[{"type": "web_search", "search_context_size": "high"}],
                        tool_choice="required",
                    )
                else:
                    resp = client.responses.create(
                        model=model,
                        input=prompt,
                        tools=[{"type": "web_search"}],
                    )
                text, sources = _responses_text_and_sources(resp)
                if text:
                    return text, sources, None
                last_err = "empty research output"
            except Exception as e:
                last_err = str(e)
                continue

    return "", [], last_err


def _chat_research_memo(client: OpenAI, model: str, req: DiagnoseRequest) -> str:
    system = """You are an expert automotive diagnostician and technical writer.
You do NOT have live web access in this mode. Apply strong general knowledge: OBD-II definitions, common failures by vehicle era and platform, interaction between symptoms, and safe workshop practice.

Write a structured research memo in Markdown with sections:
## OBD / scan context
## Platform / vehicle-family notes (for this year, make, model, engine when inferable)
## Ranked hypotheses (most likely first; short rationale each)
## Safety-critical differentials
## Verification sequence (tests/inspections in sensible order)

Be specific: name components, tests, and expected findings. State uncertainty where appropriate."""
    user = json.dumps(req.model_dump(), indent=2)
    r = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return (r.choices[0].message.content or "").strip()


def _normalize_causes_payload(causes: list[Any]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for c in causes[:3]:
        if not isinstance(c, dict):
            continue
        normalized.append(
            {
                "title": str(c.get("title", "Unknown issue"))[:220],
                "probability": int(c.get("probability", 34)),
                "explanation": str(c.get("explanation", ""))[:4000],
                "recommended_next_steps": str(
                    c.get("recommended_next_steps", c.get("next_steps", ""))
                )[:4000],
            }
        )
    while len(normalized) < 3:
        normalized.append(
            {
                "title": "Further diagnosis required",
                "probability": 20,
                "explanation": "Insufficient structured output; verify with inspection and scan data.",
                "recommended_next_steps": "Re-scan all modules, review live data, and perform targeted tests from the research memo.",
            }
        )
    probs = [max(0, min(100, int(x["probability"]))) for x in normalized[:3]]
    total_p = sum(probs) or 1
    for i in range(3):
        normalized[i]["probability"] = max(8, min(90, int(round(100 * probs[i] / total_p))))
    delta = 100 - sum(normalized[i]["probability"] for i in range(3))
    normalized[0]["probability"] = max(8, min(92, normalized[0]["probability"] + delta))
    return normalized[:3]


def _synthesize_diagnosis(
    client: OpenAI,
    model: str,
    req: DiagnoseRequest,
    research_notes: str,
    used_web_search: bool,
) -> dict[str, Any]:
    system = """You are TorqueTrace, the final synthesis engine for an automotive workshop app.

You will receive CASE JSON plus an optional RESEARCH MEMO (from live web search + expert reasoning, or expert-only).

Return ONLY valid JSON (no markdown fences) with this exact shape:
{
  "causes": [
    {
      "title": "string",
      "probability": integer 0-100,
      "explanation": "string",
      "recommended_next_steps": "string"
    }
  ],
  "severity": "Low" | "Medium" | "High",
  "estimated_repair_cost_range": "string like $200 - $800",
  "safe_to_drive": boolean,
  "summary": "string"
}

Rules:
- Exactly 3 causes, sorted by probability descending.
- Integer probabilities should sum to 100 (small rounding slack allowed).
- Ground causes, explanations, and next steps in the RESEARCH MEMO when it is substantive; reconcile with OBD codes and symptoms.
- If the memo is thin, still give the best defensible automotive judgment for this vehicle context.
- Never invent specific recall numbers or URLs; speak generically if unsure.
- Severity and safe_to_drive must reflect real risk (overheating in red zone, brake failure, large fuel leak, severe misfire under load, loss of steering assist, etc. => safe_to_drive false and usually High severity).
- estimated_repair_cost_range: realistic independent-shop ballpark in USD; use a wide band when uncertain.
- summary: 2-4 sentences, plain language, mentions top suspicion."""

    user = (
        "CASE_JSON:\n"
        + json.dumps(req.model_dump(), indent=2)
        + "\n\nRESEARCH_MEMO (may be long):\n"
        + (research_notes or "(none — use best expert judgment)")
        + "\n\nINTERNAL_FLAGS:\n"
        + json.dumps({"used_web_search": used_web_search})
    )

    resp = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.25,
    )

    content = resp.choices[0].message.content or "{}"
    data = json.loads(content)
    causes = data.get("causes") or []
    normalized = _normalize_causes_payload(causes if isinstance(causes, list) else [])

    sev = str(data.get("severity", "Medium"))
    if sev not in ("Low", "Medium", "High"):
        sev = "Medium"

    return {
        "causes": normalized,
        "severity": sev,
        "estimated_repair_cost_range": str(data.get("estimated_repair_cost_range", "$200 – $900"))[:200],
        "safe_to_drive": bool(data.get("safe_to_drive", True)),
        "summary": str(data.get("summary", "Diagnosis complete."))[:4000],
    }


def _openai_diagnosis(req: DiagnoseRequest) -> dict[str, Any]:
    # OpenAI is opt-in so the app never sends requests or uses a key unless explicitly enabled.
    if not _truthy(os.getenv("TORQUE_USE_OPENAI"), default=False):
        return _rule_based_diagnosis(req)

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return _rule_based_diagnosis(req)

    client = OpenAI(api_key=api_key)
    synth_model = _synthesis_model()
    use_web = _truthy(os.getenv("TORQUE_WEB_SEARCH"), default=True)

    research_notes = ""
    sources: list[dict[str, str]] = []
    used_web = False
    research_err: str | None = None

    if use_web:
        memo, src, err = _web_research_memo(client, req)
        if memo:
            research_notes = memo
            sources = src
            used_web = True
        else:
            research_err = err

    if not research_notes.strip():
        research_notes = _chat_research_memo(client, synth_model, req)
        used_web = False

    base = _synthesize_diagnosis(client, synth_model, req, research_notes, used_web)

    max_notes = int(os.getenv("TORQUE_RESEARCH_MAX_CHARS", "12000"))
    base["research_notes"] = research_notes[:max_notes] if research_notes else None
    base["research_sources"] = sources[:25]
    base["used_web_search"] = used_web
    if research_err and not used_web:
        base["research_engine_note"] = (
            f"Web search was requested but unavailable for the configured research models: {research_err[:500]}"
        )
    return base


def run_diagnosis(req: DiagnoseRequest) -> dict[str, Any]:
    """OpenAI (web research + synthesis) only when TORQUE_USE_OPENAI=true and OPENAI_API_KEY is set; else rules."""
    try:
        return _openai_diagnosis(req)
    except Exception:
        out = _rule_based_diagnosis(req)
        out["research_engine_note"] = (
            "OpenAI request failed; fell back to built-in rules. Check OPENAI_API_KEY, billing, and model access."
        )
        return out
