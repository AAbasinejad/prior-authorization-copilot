from app.models.schemas import PriorAuthRequestCreate
from app.services.extraction import extract_signals
from app.services.rule_engine import find_missing, get_rule
from app.services.risk_model import score_denial_risk


def build_request_payload(request: PriorAuthRequestCreate) -> dict:
    extracted = extract_signals(request.clinical_note)
    rule = get_rule(request.payer, request.procedure_code)
    missing = find_missing(rule["required_documents"], request.attached_documents, extracted)
    risk_score, risk_level = score_denial_risk(missing, extracted, request.payer)
    status = "needs_review" if missing else "ready_to_submit"
    packet_summary = {
        "patient_id": request.patient_id,
        "payer": request.payer,
        "procedure_code": request.procedure_code,
        "diagnosis_codes": request.diagnosis_codes,
        "required_documents": rule["required_documents"],
        "recommended_documents": rule["recommended_documents"],
        "medical_necessity_ready": extracted.get("has_medical_necessity_narrative", False),
    }
    return {
        "patient_id": request.patient_id,
        "payer": request.payer,
        "procedure_code": request.procedure_code,
        "diagnosis_codes": request.diagnosis_codes,
        "clinical_note": request.clinical_note,
        "attached_documents": request.attached_documents,
        "extracted_signals": extracted,
        "required_documents": rule["required_documents"],
        "missing_documents": missing,
        "denial_risk_score": risk_score,
        "risk_level": risk_level,
        "status": status,
        "packet_summary": packet_summary,
    }


def build_submission_packet(record) -> dict:
    return {
        "request_id": record.id,
        "patient_id": record.patient_id,
        "payer": record.payer,
        "procedure_code": record.procedure_code,
        "diagnosis_codes": record.diagnosis_codes,
        "required_documents": record.required_documents,
        "attached_documents": record.attached_documents,
        "missing_documents": record.missing_documents,
        "risk_level": record.risk_level,
        "ready": not bool(record.missing_documents),
    }
