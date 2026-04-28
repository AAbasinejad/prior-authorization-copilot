PAYER_RULES = {
    ("Aetna", "72148"): {"required_documents": ["clinical_notes", "conservative_treatment_6_weeks"], "recommended_documents": ["xray_report"]},
    ("UnitedHealthcare", "73721"): {"required_documents": ["clinical_notes", "physical_therapy_completed"], "recommended_documents": ["medication_history"]},
    ("Cigna", "29881"): {"required_documents": ["clinical_notes", "operative_plan"], "recommended_documents": ["imaging_report"]},
}


def get_rule(payer: str, procedure_code: str) -> dict:
    return PAYER_RULES.get((payer, procedure_code), {"required_documents": ["clinical_notes"], "recommended_documents": []})


def find_missing(required_documents: list[str], attached_documents: list[str], extracted_signals: dict) -> list[str]:
    attached = set(attached_documents)
    extracted = set(extracted_signals.get("matched_signals", []))
    return [item for item in required_documents if item not in attached and item not in extracted]
