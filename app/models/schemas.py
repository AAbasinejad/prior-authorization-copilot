from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field


class PriorAuthRequestCreate(BaseModel):
    patient_id: str = Field(..., description="Internal patient or encounter identifier.", examples=["P-1001"])
    payer: str = Field(..., description="Payer name used for rule matching.", examples=["Aetna"])
    procedure_code: str = Field(..., description="CPT/HCPCS procedure code for the authorization request.", examples=["72148"])
    diagnosis_codes: list[str] = Field(
        default_factory=list,
        description="ICD diagnosis codes supporting medical necessity.",
        examples=[["M54.50", "M51.36"]],
    )
    clinical_note: str = Field(
        ...,
        description="Clinical narrative used to extract medical necessity and treatment signals.",
        examples=[
            "Patient has chronic lumbar pain. Completed 8 weeks physical therapy and NSAIDs with no improvement."
        ],
    )
    attached_documents: list[str] = Field(
        default_factory=list,
        description="Document keys already available in the packet.",
        examples=[["clinical_notes", "xray_report"]],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "patient_id": "P-1001",
                    "payer": "Aetna",
                    "procedure_code": "72148",
                    "diagnosis_codes": ["M54.50"],
                    "clinical_note": "Patient has chronic lumbar pain. Completed 8 weeks physical therapy and NSAIDs with no improvement.",
                    "attached_documents": ["clinical_notes", "xray_report"],
                }
            ]
        }
    }


class PriorAuthPreviewResponse(BaseModel):
    patient_id: str = Field(..., examples=["P-1001"])
    payer: str = Field(..., examples=["Aetna"])
    procedure_code: str = Field(..., examples=["72148"])
    diagnosis_codes: list[str] = Field(default_factory=list, examples=[["M54.50"]])
    extracted_signals: dict[str, Any] = Field(
        ...,
        examples=[
            {
                "note_length": 103,
                "matched_signals": ["physical_therapy_completed", "nsaid_trialed", "conservative_treatment_6_weeks"],
                "has_medical_necessity_narrative": True,
                "conservative_treatment_documented": True,
            }
        ],
    )
    required_documents: list[str] = Field(..., examples=[["clinical_notes", "conservative_treatment_6_weeks"]])
    recommended_documents: list[str] = Field(default_factory=list, examples=[["xray_report"]])
    missing_documents: list[str] = Field(default_factory=list, examples=[[]])
    denial_risk_score: float = Field(..., ge=0, le=1, examples=[0.17])
    risk_level: str = Field(..., examples=["low"])
    status: str = Field(..., examples=["ready_to_submit"])
    ready_to_submit: bool = Field(..., examples=[True])
    recommended_actions: list[str] = Field(
        default_factory=list,
        examples=[["Packet is ready for payer submission.", "Attach recommended document(s) if available: xray_report."]],
    )
    packet_summary: dict[str, Any] = Field(..., description="Condensed packet view for dashboard and submission review.")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "patient_id": "P-1001",
                    "payer": "Aetna",
                    "procedure_code": "72148",
                    "diagnosis_codes": ["M54.50"],
                    "extracted_signals": {
                        "note_length": 103,
                        "matched_signals": [
                            "physical_therapy_completed",
                            "nsaid_trialed",
                            "conservative_treatment_6_weeks",
                        ],
                        "has_medical_necessity_narrative": True,
                        "conservative_treatment_documented": True,
                    },
                    "required_documents": ["clinical_notes", "conservative_treatment_6_weeks"],
                    "recommended_documents": ["xray_report"],
                    "missing_documents": [],
                    "denial_risk_score": 0.17,
                    "risk_level": "low",
                    "status": "ready_to_submit",
                    "ready_to_submit": True,
                    "recommended_actions": [
                        "Packet is ready for payer submission.",
                        "Attach recommended document(s) if available: xray_report.",
                    ],
                    "packet_summary": {
                        "medical_necessity_ready": True,
                        "ready": True,
                        "missing_documents": [],
                    },
                }
            ]
        }
    }


class PriorAuthRequestResponse(BaseModel):
    id: int = Field(..., examples=[101])
    patient_id: str = Field(..., examples=["P-1001"])
    payer: str = Field(..., examples=["Aetna"])
    procedure_code: str = Field(..., examples=["72148"])
    diagnosis_codes: list[str] = Field(default_factory=list, examples=[["M54.50"]])
    clinical_note: str = Field(..., examples=["Patient completed 8 weeks physical therapy with no improvement."])
    attached_documents: list[str] = Field(default_factory=list, examples=[["clinical_notes", "xray_report"]])
    extracted_signals: dict[str, Any] = Field(..., examples=[{"matched_signals": ["conservative_treatment_6_weeks"]}])
    required_documents: list[str] = Field(..., examples=[["clinical_notes", "conservative_treatment_6_weeks"]])
    missing_documents: list[str] = Field(default_factory=list, examples=[[]])
    denial_risk_score: float = Field(..., ge=0, le=1, examples=[0.17])
    risk_level: str = Field(..., examples=["low"])
    status: str = Field(..., examples=["ready_to_submit"])
    packet_summary: dict[str, Any] = Field(..., examples=[{"ready": True, "recommended_actions": ["Packet is ready for payer submission."]}])
    created_at: datetime = Field(..., examples=["2026-04-22T09:30:00"])
    updated_at: datetime = Field(..., examples=["2026-04-22T09:30:00"])

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 101,
                    "patient_id": "P-1001",
                    "payer": "Aetna",
                    "procedure_code": "72148",
                    "diagnosis_codes": ["M54.50"],
                    "clinical_note": "Patient has chronic lumbar pain. Completed 8 weeks physical therapy and NSAIDs with no improvement.",
                    "attached_documents": ["clinical_notes", "xray_report"],
                    "extracted_signals": {
                        "note_length": 103,
                        "matched_signals": [
                            "physical_therapy_completed",
                            "nsaid_trialed",
                            "conservative_treatment_6_weeks",
                        ],
                        "has_medical_necessity_narrative": True,
                        "conservative_treatment_documented": True,
                    },
                    "required_documents": ["clinical_notes", "conservative_treatment_6_weeks"],
                    "missing_documents": [],
                    "denial_risk_score": 0.17,
                    "risk_level": "low",
                    "status": "ready_to_submit",
                    "packet_summary": {
                        "ready": True,
                        "medical_necessity_ready": True,
                        "recommended_documents": ["xray_report"],
                        "recommended_actions": [
                            "Packet is ready for payer submission.",
                            "Attach recommended document(s) if available: xray_report.",
                        ],
                    },
                    "created_at": "2026-04-22T09:30:00",
                    "updated_at": "2026-04-22T09:30:00",
                }
            ]
        },
    }


class PatientRiskPreviewRequest(BaseModel):
    patient_id: str = Field(..., description="Internal patient or encounter identifier.", examples=["P-1001"])
    patient_age: int = Field(..., ge=0, le=120, description="Patient age in years.", examples=[67])
    payer: str = Field(..., description="Payer name used for authorization risk context.", examples=["Aetna"])
    procedure_code: str = Field(..., description="CPT/HCPCS procedure code.", examples=["72148"])
    diagnosis_codes: list[str] = Field(default_factory=list, examples=[["M54.50"]])
    prior_denials_12m: int = Field(0, ge=0, le=50, description="Count of prior authorization denials in the last 12 months.", examples=[1])
    chronic_condition_count: int = Field(0, ge=0, le=30, description="Simple proxy for patient clinical complexity.", examples=[3])
    recent_ed_visits_6m: int = Field(0, ge=0, le=50, description="Emergency department visits in the last 6 months.", examples=[1])
    urgency: Literal["routine", "urgent", "emergent"] = Field("routine", examples=["routine"])
    clinical_note: str = Field(
        ...,
        description="Clinical narrative used to align patient-level friction with packet risk.",
        examples=[
            "Patient has chronic lumbar pain. Completed 8 weeks physical therapy and NSAIDs with no improvement."
        ],
    )
    attached_documents: list[str] = Field(default_factory=list, examples=[["clinical_notes", "xray_report"]])

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "patient_id": "P-1001",
                    "patient_age": 67,
                    "payer": "Aetna",
                    "procedure_code": "72148",
                    "diagnosis_codes": ["M54.50"],
                    "prior_denials_12m": 1,
                    "chronic_condition_count": 3,
                    "recent_ed_visits_6m": 1,
                    "urgency": "routine",
                    "clinical_note": "Patient has chronic lumbar pain. Completed 8 weeks physical therapy and NSAIDs with no improvement.",
                    "attached_documents": ["clinical_notes", "xray_report"],
                }
            ]
        }
    }


class PatientRiskPreviewResponse(BaseModel):
    patient_id: str = Field(..., examples=["P-1001"])
    patient_complexity_score: float = Field(..., ge=0, le=1, examples=[0.245])
    predicted_prior_auth_friction: float = Field(..., ge=0, le=1, examples=[0.20])
    complexity_level: str = Field(..., examples=["low"])
    drivers: list[str] = Field(default_factory=list, examples=[["older_adult", "recent_prior_denials"]])
    recommended_actions: list[str] = Field(
        default_factory=list,
        examples=[["Review denial history and include appeal-relevant evidence before submission."]],
    )
    authorization_risk_score: float = Field(..., ge=0, le=1, examples=[0.17])
    authorization_risk_level: str = Field(..., examples=["low"])
    missing_documents: list[str] = Field(default_factory=list, examples=[[]])

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "patient_id": "P-1001",
                    "patient_complexity_score": 0.245,
                    "predicted_prior_auth_friction": 0.20,
                    "complexity_level": "low",
                    "drivers": ["older_adult", "recent_prior_denials", "clinical_complexity"],
                    "recommended_actions": [
                        "Review denial history and include appeal-relevant evidence before submission.",
                        "Add a concise clinical-complexity summary to the packet narrative.",
                    ],
                    "authorization_risk_score": 0.17,
                    "authorization_risk_level": "low",
                    "missing_documents": [],
                }
            ]
        }
    }


class SubmissionResponse(BaseModel):
    request_id: int = Field(..., examples=[101])
    status: str = Field(..., examples=["submitted"])
    submitted_packet: dict[str, Any] = Field(
        ...,
        examples=[
            {
                "request_id": 101,
                "patient_id": "P-1001",
                "payer": "Aetna",
                "procedure_code": "72148",
                "ready": True,
                "missing_documents": [],
            }
        ],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "request_id": 101,
                    "status": "submitted",
                    "submitted_packet": {
                        "request_id": 101,
                        "patient_id": "P-1001",
                        "payer": "Aetna",
                        "procedure_code": "72148",
                        "diagnosis_codes": ["M54.50"],
                        "required_documents": ["clinical_notes", "conservative_treatment_6_weeks"],
                        "attached_documents": ["clinical_notes", "xray_report"],
                        "missing_documents": [],
                        "risk_level": "low",
                        "ready": True,
                    },
                }
            ]
        }
    }


class OpsSummary(BaseModel):
    total_requests: int = Field(..., examples=[24])
    by_status: dict[str, int] = Field(..., examples=[{"ready_to_submit": 14, "needs_review": 7, "submitted": 3}])
    by_risk: dict[str, int] = Field(..., examples=[{"low": 12, "medium": 9, "high": 3}])
    average_risk_score: float = Field(..., ge=0, le=1, examples=[0.3842])

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "total_requests": 24,
                    "by_status": {"ready_to_submit": 14, "needs_review": 7, "submitted": 3},
                    "by_risk": {"low": 12, "medium": 9, "high": 3},
                    "average_risk_score": 0.3842,
                }
            ]
        }
    }


class HealthResponse(BaseModel):
    status: str = Field(..., examples=["ok"])

    model_config = {"json_schema_extra": {"examples": [{"status": "ok"}]}}
