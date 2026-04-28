from datetime import datetime
from sqlalchemy import JSON, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from prior_auth_copilot.core.database import Base


class PriorAuthRequestDB(Base):
    __tablename__ = "prior_auth_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[str] = mapped_column(String(50), index=True)
    payer: Mapped[str] = mapped_column(String(100), index=True)
    procedure_code: Mapped[str] = mapped_column(String(20), index=True)
    diagnosis_codes: Mapped[list] = mapped_column(JSON)
    clinical_note: Mapped[str] = mapped_column(Text)
    attached_documents: Mapped[list] = mapped_column(JSON)
    extracted_signals: Mapped[dict] = mapped_column(JSON, default=dict)
    missing_documents: Mapped[list] = mapped_column(JSON, default=list)
    required_documents: Mapped[list] = mapped_column(JSON, default=list)
    denial_risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    risk_level: Mapped[str] = mapped_column(String(20), default="low")
    status: Mapped[str] = mapped_column(String(30), default="draft")
    packet_summary: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
