"""OpenAI-backed diagnosis with rule-based fallback when no API key is set."""

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
        "This is not a substitute for a hands-on inspection."
    )

    return {
        "causes": causes[:3],
        "severity": severity,
        "estimated_repair_cost_range": cost,
        "safe_to_drive": safe_to_drive,
        "summary": summary,
    }


def _openai_diagnosis(req: DiagnoseRequest) -> dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return _rule_based_diagnosis(req)

    client = OpenAI(api_key=api_key)
    user_payload = req.model_dump()

    system = """You are AutoIntel AI, an expert automotive diagnostician.
Return ONLY valid JSON with this exact shape:
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
- Provide exactly 3 items in causes, sorted by probability descending.
- Probabilities are best-estimates and should sum to roughly 100 (allow small rounding slack).
- Be practical and safety-conscious; if overheating, major brake loss, or large fluid leaks are implied, set safe_to_drive false.
- Mention when professional inspection is required.
"""

    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user_payload)},
        ],
        temperature=0.35,
    )

    content = resp.choices[0].message.content or "{}"
    data = json.loads(content)

    causes = data.get("causes") or []
    if len(causes) != 3:
        return _rule_based_diagnosis(req)

    normalized: list[dict[str, Any]] = []
    for c in causes[:3]:
        normalized.append(
            {
                "title": str(c.get("title", "Unknown issue"))[:220],
                "probability": int(c.get("probability", 34)),
                "explanation": str(c.get("explanation", ""))[:2000],
                "recommended_next_steps": str(
                    c.get("recommended_next_steps", c.get("next_steps", ""))
                )[:2000],
            }
        )
    probs = [max(0, min(100, x["probability"])) for x in normalized]
    total_p = sum(probs) or 1
    for i, row in enumerate(normalized):
        row["probability"] = max(8, min(90, int(round(100 * probs[i] / total_p))))
    delta = 100 - sum(r["probability"] for r in normalized)
    normalized[0]["probability"] = max(8, min(92, normalized[0]["probability"] + delta))

    sev = str(data.get("severity", "Medium"))
    if sev not in ("Low", "Medium", "High"):
        sev = "Medium"

    return {
        "causes": normalized,
        "severity": sev,
        "estimated_repair_cost_range": str(
            data.get("estimated_repair_cost_range", "$200 – $800")
        )[:200],
        "safe_to_drive": bool(data.get("safe_to_drive", True)),
        "summary": str(data.get("summary", "Diagnosis complete."))[:2000],
    }


def run_diagnosis(req: DiagnoseRequest) -> dict[str, Any]:
    """Prefer OpenAI when configured; otherwise deterministic rules."""
    try:
        return _openai_diagnosis(req)
    except Exception:
        return _rule_based_diagnosis(req)
