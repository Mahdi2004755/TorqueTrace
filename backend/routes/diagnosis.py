from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

import ai_service
from database import get_db
from models import Diagnosis
from schemas import DiagnoseRequest, DiagnosisRead

router = APIRouter(tags=["diagnosis"])


@router.post("/diagnose", response_model=DiagnosisRead, status_code=status.HTTP_201_CREATED)
def create_diagnosis(payload: DiagnoseRequest, db: Session = Depends(get_db)):
    result = ai_service.run_diagnosis(payload)
    row = Diagnosis(
        vehicle_year=payload.vehicle_year,
        make=payload.make.strip(),
        model=payload.model.strip(),
        engine=(payload.engine or "").strip() or None,
        mileage=payload.mileage,
        symptoms=(payload.symptoms or "").strip() or None,
        obd_codes=(payload.obd_codes or "").strip() or None,
        noise_description=(payload.noise_description or "").strip() or None,
        smell_description=(payload.smell_description or "").strip() or None,
        ai_result=result,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/diagnoses", response_model=list[DiagnosisRead])
def list_diagnoses(db: Session = Depends(get_db)):
    stmt = select(Diagnosis).order_by(Diagnosis.created_at.desc())
    return list(db.scalars(stmt).all())


@router.get("/diagnoses/{diagnosis_id}", response_model=DiagnosisRead)
def get_diagnosis(diagnosis_id: int, db: Session = Depends(get_db)):
    row = db.get(Diagnosis, diagnosis_id)
    if not row:
        raise HTTPException(status_code=404, detail="Diagnosis not found")
    return row


@router.delete("/diagnoses/{diagnosis_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_diagnosis(diagnosis_id: int, db: Session = Depends(get_db)):
    row = db.get(Diagnosis, diagnosis_id)
    if not row:
        raise HTTPException(status_code=404, detail="Diagnosis not found")
    db.delete(row)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
