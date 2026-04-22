from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class PriorAuthRequestCreate(BaseModel):
    patient_id: str = Field(..., examples=["P-1001"])
    payer: str = Field(..., examples=["Aetna"])
    procedure_code: str = Field(..., examples=["72148"])
    diagnosis_codes: list[str] = Field(default_factory=list)
    clinical_note: str
    attached_documents: list[str] = Field(default_factory=list)


class PriorAuthRequestResponse(BaseModel):
    id: int
    patient_id: str
    payer: str
    procedure_code: str
    diagnosis_codes: list[str]
    clinical_note: str
    attached_documents: list[str]
    extracted_signals: dict[str, Any]
    required_documents: list[str]
    missing_documents: list[str]
    denial_risk_score: float
    risk_level: str
    status: str
    packet_summary: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SubmissionResponse(BaseModel):
    request_id: int
    status: str
    submitted_packet: dict[str, Any]


class OpsSummary(BaseModel):
    total_requests: int
    by_status: dict[str, int]
    by_risk: dict[str, int]
    average_risk_score: float
