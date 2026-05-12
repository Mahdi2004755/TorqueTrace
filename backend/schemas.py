from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class DiagnoseRequest(BaseModel):
    vehicle_year: int = Field(..., ge=1900, le=2035)
    make: str = Field(..., min_length=1, max_length=120)
    model: str = Field(..., min_length=1, max_length=120)
    engine: Optional[str] = None
    mileage: Optional[int] = Field(None, ge=0)
    symptoms: Optional[str] = None
    obd_codes: Optional[str] = None
    noise_description: Optional[str] = None
    smell_description: Optional[str] = None


class LikelyCause(BaseModel):
    title: str
    probability: int = Field(..., ge=0, le=100)
    explanation: str
    recommended_next_steps: str


class AIResultPayload(BaseModel):
    causes: list[LikelyCause]
    severity: str
    estimated_repair_cost_range: str
    safe_to_drive: bool
    summary: str


class DiagnosisRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vehicle_year: int
    make: str
    model: str
    engine: Optional[str]
    mileage: Optional[int]
    symptoms: Optional[str]
    obd_codes: Optional[str]
    noise_description: Optional[str]
    smell_description: Optional[str]
    ai_result: dict[str, Any]
    created_at: datetime
