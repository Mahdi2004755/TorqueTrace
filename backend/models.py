from sqlalchemy import Column, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB

from database import Base


class Diagnosis(Base):
    __tablename__ = "diagnoses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    vehicle_year = Column(Integer, nullable=False)
    make = Column(String(120), nullable=False)
    model = Column(String(120), nullable=False)
    engine = Column(String(200), nullable=True)
    mileage = Column(Integer, nullable=True)
    symptoms = Column(Text, nullable=True)
    obd_codes = Column(String(500), nullable=True)
    noise_description = Column(Text, nullable=True)
    smell_description = Column(Text, nullable=True)
    ai_result = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
