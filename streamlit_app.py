import os
import requests
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
st.set_page_config(page_title="Prior Auth Copilot", layout="wide")
st.title("Prior Auth Copilot")


def get_json(path: str):
    r = requests.get(f"{API_BASE_URL}{path}", timeout=10)
    r.raise_for_status()
    return r.json()


def post_json(path: str, payload: dict):
    r = requests.post(f"{API_BASE_URL}{path}", json=payload, timeout=20)
    r.raise_for_status()
    return r.json()


col1, col2 = st.columns([1, 1.4])
with col1:
    st.subheader("Create Prior Auth Request")
    with st.form("new_request"):
        patient_id = st.text_input("Patient ID", value="P-1001")
        payer = st.selectbox("Payer", ["Aetna", "UnitedHealthcare", "Cigna"])
        procedure_code = st.selectbox("Procedure Code", ["72148", "73721", "29881"])
        diagnosis_codes = st.text_input("Diagnosis Codes (comma-separated)", value="M54.50")
        clinical_note = st.text_area("Clinical Note", value="Patient has chronic lumbar pain. Completed 8 weeks physical therapy and NSAIDs with no improvement.", height=160)
        attached_documents = st.multiselect("Attached Documents", ["clinical_notes", "xray_report", "operative_plan", "imaging_report", "medication_history"], default=["clinical_notes"])
        submitted = st.form_submit_button("Analyze Request")
    if submitted:
        payload = {
            "patient_id": patient_id,
            "payer": payer,
            "procedure_code": procedure_code,
            "diagnosis_codes": [x.strip() for x in diagnosis_codes.split(",") if x.strip()],
            "clinical_note": clinical_note,
            "attached_documents": attached_documents,
        }
        result = post_json("/requests", payload)
        st.success(f"Request #{result['id']} created with {result['risk_level']} risk.")
        st.json(result)
with col2:
    st.subheader("Operational View")
    summary = get_json("/ops/summary")
    m = st.columns(4)
    m[0].metric("Total Requests", summary["total_requests"])
    m[1].metric("Avg Risk", summary["average_risk_score"])
    m[2].metric("Ready", summary["by_status"].get("ready_to_submit", 0))
    m[3].metric("Needs Review", summary["by_status"].get("needs_review", 0))
    st.dataframe(get_json("/requests"), use_container_width=True)
