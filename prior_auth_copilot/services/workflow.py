from prior_auth_copilot.models.schemas import PriorAuthRequestCreate
from prior_auth_copilot.services.extraction import extract_signals
from prior_auth_copilot.services.rule_engine import find_missing, get_rule
from prior_auth_copilot.services.risk_model import score_denial_risk


def build_recommended_actions(missing_documents: list[str], risk_level: str, recommended_documents: list[str]) -> list[str]:
    actions = []
    if missing_documents:
        actions.append(f"Collect required document(s): {', '.join(missing_documents)}.")
    else:
        actions.append("Packet is ready for payer submission.")

    if risk_level == "high":
        actions.append("Route to clinical review before submission because denial risk is elevated.")
    elif risk_level == "medium":
        actions.append("Review medical-necessity language and payer-specific documentation before submission.")

    if recommended_documents:
        actions.append(f"Attach recommended document(s) if available: {', '.join(recommended_documents)}.")
    return actions


def build_request_payload(request: PriorAuthRequestCreate) -> dict:
    extracted = extract_signals(request.clinical_note)
    rule = get_rule(request.payer, request.procedure_code)
    missing = find_missing(rule["required_documents"], request.attached_documents, extracted)
    risk_score, risk_level = score_denial_risk(missing, extracted, request.payer)
    status = "needs_review" if missing else "ready_to_submit"
    recommended_actions = build_recommended_actions(missing, risk_level, rule["recommended_documents"])
    packet_summary = {
        "patient_id": request.patient_id,
        "payer": request.payer,
        "procedure_code": request.procedure_code,
        "diagnosis_codes": request.diagnosis_codes,
        "required_documents": rule["required_documents"],
        "recommended_documents": rule["recommended_documents"],
        "missing_documents": missing,
        "medical_necessity_ready": extracted.get("has_medical_necessity_narrative", False),
        "ready": not bool(missing),
        "recommended_actions": recommended_actions,
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


def build_preview_response(request: PriorAuthRequestCreate) -> dict:
    payload = build_request_payload(request)
    packet_summary = payload["packet_summary"]
    return {
        "patient_id": payload["patient_id"],
        "payer": payload["payer"],
        "procedure_code": payload["procedure_code"],
        "diagnosis_codes": payload["diagnosis_codes"],
        "extracted_signals": payload["extracted_signals"],
        "required_documents": payload["required_documents"],
        "recommended_documents": packet_summary["recommended_documents"],
        "missing_documents": payload["missing_documents"],
        "denial_risk_score": payload["denial_risk_score"],
        "risk_level": payload["risk_level"],
        "status": payload["status"],
        "ready_to_submit": packet_summary["ready"],
        "recommended_actions": packet_summary["recommended_actions"],
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
        "recommended_actions": record.packet_summary.get("recommended_actions", []),
    }
