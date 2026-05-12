"""
Insert sample diagnoses for local testing.
Run from backend directory: python seed_db.py
"""

from sqlalchemy import func, select

from database import SessionLocal, engine, Base
from models import Diagnosis


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.scalar(select(func.count()).select_from(Diagnosis)) or 0
        if existing > 0:
            print("Diagnoses table already has rows; skipping seed.")
            return

        samples = [
            {
                "vehicle_year": 2016,
                "make": "Honda",
                "model": "Civic",
                "engine": "2.0L I4",
                "mileage": 112000,
                "symptoms": "Check engine light, rough idle at stoplights",
                "obd_codes": "P0420",
                "noise_description": "",
                "smell_description": "Slight sulfur smell after hard acceleration",
                "ai_result": {
                    "causes": [
                        {
                            "title": "Catalyst system efficiency below threshold (Bank 1)",
                            "probability": 55,
                            "explanation": "P0420 with sulfur odor often correlates with catalytic converter efficiency loss or temporary rich events.",
                            "recommended_next_steps": "Verify exhaust leaks, review O2 sensor behavior, and confirm no misfires before replacing the cat.",
                        },
                        {
                            "title": "Rich running or catalytic converter odor (sulfur compounds)",
                            "probability": 30,
                            "explanation": "Sulfur smell can appear when the mixture is rich or the converter is processing excess sulfur compounds.",
                            "recommended_next_steps": "Check fuel trims, inspect spark plugs for fouling, and scan for additional codes.",
                        },
                        {
                            "title": "Idle air / vacuum leak or ignition-fuel imbalance",
                            "probability": 15,
                            "explanation": "Rough idle can be independent or worsen catalyst stress if misfires are present.",
                            "recommended_next_steps": "Smoke test for vacuum leaks and evaluate idle air trims.",
                        },
                    ],
                    "severity": "Medium",
                    "estimated_repair_cost_range": "$350 – $1,400",
                    "safe_to_drive": True,
                    "summary": "Sample: P0420 with rough idle and sulfur smell — prioritize exhaust/O2/cat pathway.",
                },
            },
            {
                "vehicle_year": 2014,
                "make": "Ford",
                "model": "F-150",
                "engine": "5.0L V8",
                "mileage": 156000,
                "symptoms": "Misfire felt under load",
                "obd_codes": "P0300, P0430",
                "noise_description": "Ticking noise that changes with RPM",
                "smell_description": "",
                "ai_result": {
                    "causes": [
                        {
                            "title": "Random / multiple cylinder misfire detected",
                            "probability": 48,
                            "explanation": "P0300 indicates multiple cylinders misfiring; under load this often implicates ignition or fuel delivery.",
                            "recommended_next_steps": "Read misfire counters, swap coils/plugs as a test, and check fuel pressure.",
                        },
                        {
                            "title": "Catalyst system efficiency below threshold (Bank 2)",
                            "probability": 32,
                            "explanation": "P0430 may follow prolonged misfires that stress the Bank 2 catalyst.",
                            "recommended_next_steps": "Resolve misfires first, then retest catalyst monitors.",
                        },
                        {
                            "title": "Valve train tick or accessory/component noise",
                            "probability": 20,
                            "explanation": "RPM-following ticks can be valvetrain, injectors, or exhaust leaks—isolate with a stethoscope.",
                            "recommended_next_steps": "Verify oil level/pressure and pinpoint tick source before major repairs.",
                        },
                    ],
                    "severity": "High",
                    "estimated_repair_cost_range": "$500 – $2,200+",
                    "safe_to_drive": False,
                    "summary": "Sample: P0300 + P0430 with ticking — treat misfire as urgent; verify mechanical noise separately.",
                },
            },
            {
                "vehicle_year": 2011,
                "make": "Toyota",
                "model": "Camry",
                "engine": "2.5L I4",
                "mileage": 189000,
                "symptoms": "Temperature climbs in traffic, rough idle when hot",
                "obd_codes": "",
                "noise_description": "",
                "smell_description": "",
                "ai_result": {
                    "causes": [
                        {
                            "title": "Cooling system fault or head gasket breach",
                            "probability": 60,
                            "explanation": "Overheating in traffic commonly involves fans, thermostat, water pump, or radiator flow restrictions.",
                            "recommended_next_steps": "After cool-down, check coolant level, fan operation, and thermostat; pressure test if suspected gasket.",
                        },
                        {
                            "title": "Idle air / vacuum leak or ignition-fuel imbalance",
                            "probability": 25,
                            "explanation": "Hot rough idle can be separate from cooling faults but may worsen heat soak symptoms.",
                            "recommended_next_steps": "Review idle trims hot vs cold and inspect for vacuum leaks.",
                        },
                        {
                            "title": "General drivability / maintenance-related issue",
                            "probability": 15,
                            "explanation": "Deferred maintenance (coolant age, belts) can contribute to marginal cooling performance.",
                            "recommended_next_steps": "Service coolant per manufacturer and inspect drive belt tensioner.",
                        },
                    ],
                    "severity": "High",
                    "estimated_repair_cost_range": "$200 – $1,800+",
                    "safe_to_drive": False,
                    "summary": "Sample: overheating scenario — avoid driving until cooling system is verified safe.",
                },
            },
        ]

        for s in samples:
            db.add(Diagnosis(**s))
        db.commit()
        print(f"Seeded {len(samples)} sample diagnoses.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
