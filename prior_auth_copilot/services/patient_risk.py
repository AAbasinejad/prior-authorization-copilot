from prior_auth_copilot.models.schemas import PatientRiskPreviewRequest, PriorAuthRequestCreate
from prior_auth_copilot.services.workflow import build_preview_response


def score_patient_prior_auth_friction(request: PatientRiskPreviewRequest) -> dict:
    auth_payload = PriorAuthRequestCreate(
        patient_id=request.patient_id,
        payer=request.payer,
        procedure_code=request.procedure_code,
        diagnosis_codes=request.diagnosis_codes,
        clinical_note=request.clinical_note,
        attached_documents=request.attached_documents,
    )
    auth_preview = build_preview_response(auth_payload)

    clinical_score = 0.10
    drivers = []

    if request.patient_age >= 75:
        clinical_score += 0.07
        drivers.append("advanced_age")
    elif request.patient_age >= 65:
        clinical_score += 0.04
        drivers.append("older_adult")
    elif request.patient_age < 18:
        clinical_score += 0.05
        drivers.append("pediatric_case")

    if request.prior_denials_12m:
        clinical_score += min(request.prior_denials_12m * 0.08, 0.32)
        drivers.append("recent_prior_denials")

    if request.chronic_condition_count:
        clinical_score += min(request.chronic_condition_count * 0.025, 0.20)
        drivers.append("clinical_complexity")

    if request.recent_ed_visits_6m:
        clinical_score += min(request.recent_ed_visits_6m * 0.03, 0.18)
        drivers.append("recent_acute_utilization")

    if request.urgency == "urgent":
        clinical_score += 0.05
        drivers.append("urgent_request")
    elif request.urgency == "emergent":
        clinical_score += 0.08
        drivers.append("emergent_request")

    if auth_preview["missing_documents"]:
        clinical_score += 0.10
        drivers.append("authorization_packet_gap")

    clinical_score = min(clinical_score, 0.98)
    friction_score = min(round((0.60 * auth_preview["denial_risk_score"]) + (0.40 * clinical_score), 4), 0.98)
    complexity_level = "high" if friction_score >= 0.65 else "medium" if friction_score >= 0.35 else "low"

    actions = []
    if "recent_prior_denials" in drivers:
        actions.append("Review denial history and include appeal-relevant evidence before submission.")
    if "clinical_complexity" in drivers or "recent_acute_utilization" in drivers:
        actions.append("Add a concise clinical-complexity summary to the packet narrative.")
    if auth_preview["missing_documents"]:
        actions.append(f"Resolve required packet gaps: {', '.join(auth_preview['missing_documents'])}.")
    if not actions:
        actions.append("Patient-level friction appears controlled; continue with standard packet review.")

    return {
        "patient_id": request.patient_id,
        "patient_complexity_score": round(clinical_score, 4),
        "predicted_prior_auth_friction": friction_score,
        "complexity_level": complexity_level,
        "drivers": drivers,
        "recommended_actions": actions,
        "authorization_risk_score": auth_preview["denial_risk_score"],
        "authorization_risk_level": auth_preview["risk_level"],
        "missing_documents": auth_preview["missing_documents"],
    }
