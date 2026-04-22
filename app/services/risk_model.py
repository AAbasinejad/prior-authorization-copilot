def score_denial_risk(missing_documents: list[str], extracted_signals: dict, payer: str) -> tuple[float, str]:
    score = 0.12
    score += min(0.18 * len(missing_documents), 0.54)
    if not extracted_signals.get("has_medical_necessity_narrative"):
        score += 0.15
    if not extracted_signals.get("conservative_treatment_documented"):
        score += 0.12
    if payer.lower() in {"aetna", "unitedhealthcare"}:
        score += 0.05
    score = min(round(score, 4), 0.98)
    level = "high" if score >= 0.65 else "medium" if score >= 0.35 else "low"
    return score, level
