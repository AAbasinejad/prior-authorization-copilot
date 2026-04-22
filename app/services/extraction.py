KEYWORD_MAP = {
    "physical therapy": "physical_therapy_completed",
    "pt": "physical_therapy_completed",
    "nsaid": "nsaid_trialed",
    "xray": "xray_completed",
    "mri": "mri_requested",
    "6 weeks": "conservative_treatment_6_weeks",
    "8 weeks": "conservative_treatment_6_weeks",
    "failed": "treatment_failed",
    "no improvement": "treatment_failed",
}


def extract_signals(clinical_note: str) -> dict:
    text = clinical_note.lower()
    signals = {"note_length": len(clinical_note), "matched_signals": []}
    for phrase, signal in KEYWORD_MAP.items():
        if phrase in text:
            signals["matched_signals"].append(signal)
    signals["has_medical_necessity_narrative"] = any(word in text for word in ["pain", "failed", "worsening", "unable"])
    signals["conservative_treatment_documented"] = "conservative_treatment_6_weeks" in signals["matched_signals"]
    return signals
