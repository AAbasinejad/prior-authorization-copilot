import os

import pandas as pd
import requests
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
DOC_OPTIONS = [
    "clinical_notes",
    "conservative_treatment_6_weeks",
    "physical_therapy_completed",
    "xray_report",
    "operative_plan",
    "imaging_report",
    "medication_history",
]

st.set_page_config(page_title="Prior Auth Copilot", layout="wide")


def get_json(path: str):
    response = requests.get(f"{API_BASE_URL}{path}", timeout=10)
    response.raise_for_status()
    return response.json()


def post_json(path: str, payload: dict):
    response = requests.post(f"{API_BASE_URL}{path}", json=payload, timeout=20)
    response.raise_for_status()
    return response.json()


def api_is_available() -> bool:
    try:
        return get_json("/health").get("status") == "ok"
    except requests.RequestException:
        return False


def parse_codes(raw_codes: str) -> list[str]:
    return [code.strip() for code in raw_codes.split(",") if code.strip()]


def build_payload(
    patient_id: str,
    payer: str,
    procedure_code: str,
    diagnosis_codes: str,
    clinical_note: str,
    attached_documents: list[str],
) -> dict:
    return {
        "patient_id": patient_id,
        "payer": payer,
        "procedure_code": procedure_code,
        "diagnosis_codes": parse_codes(diagnosis_codes),
        "clinical_note": clinical_note,
        "attached_documents": attached_documents,
    }


def render_preview(preview: dict):
    score = float(preview["denial_risk_score"])
    metric_cols = st.columns(3)
    metric_cols[0].metric("Denial Risk", f"{score:.0%}")
    metric_cols[1].metric("Risk Level", preview["risk_level"].title())
    metric_cols[2].metric("Packet Status", preview["status"].replace("_", " ").title())
    st.progress(score)

    readiness_color = "green" if preview["ready_to_submit"] else "orange"
    readiness_label = "Ready" if preview["ready_to_submit"] else "Needs Review"
    st.markdown(f"**Readiness:** :{readiness_color}[{readiness_label}]")

    st.subheader("Next Best Actions")
    for action in preview["recommended_actions"]:
        st.write(f"- {action}")

    detail_cols = st.columns(2)
    with detail_cols[0]:
        st.subheader("Missing Documents")
        if preview["missing_documents"]:
            st.warning(", ".join(preview["missing_documents"]))
        else:
            st.success("No required documents are missing.")
        st.subheader("Required Documents")
        st.write(", ".join(preview["required_documents"]) or "None")
        st.subheader("Recommended Documents")
        st.write(", ".join(preview["recommended_documents"]) or "None")

    with detail_cols[1]:
        st.subheader("Extracted Clinical Signals")
        signals = preview["extracted_signals"]
        st.write(f"Matched signals: {', '.join(signals.get('matched_signals', [])) or 'None'}")
        st.write(f"Medical necessity narrative: {'Yes' if signals.get('has_medical_necessity_narrative') else 'No'}")
        st.write(f"Conservative treatment documented: {'Yes' if signals.get('conservative_treatment_documented') else 'No'}")
        st.write(f"Clinical note length: {signals.get('note_length', 0)} characters")


def to_request_table(records: list[dict]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    columns = [
        "id",
        "patient_id",
        "payer",
        "procedure_code",
        "risk_level",
        "denial_risk_score",
        "status",
        "missing_documents",
        "created_at",
    ]
    return df[[column for column in columns if column in df.columns]]


st.title("Prior Auth Copilot")
st.caption("Real-time prior authorization intake, payer documentation checks, denial-risk scoring, and packet readiness review.")

api_available = api_is_available()
with st.sidebar:
    st.header("Backend")
    st.code(API_BASE_URL)
    if api_available:
        st.success("FastAPI backend is healthy.")
    else:
        st.error("FastAPI backend is offline.")
        st.write("Start it with:")
        st.code("uvicorn app.api.main:app --reload --port 8000")

    st.header("Workflow")
    st.write("1. Preview denial risk before saving.")
    st.write("2. Create the request packet.")
    st.write("3. Review missing documents.")
    st.write("4. Submit when ready.")

if not api_available:
    st.warning("The dashboard is running, but live predictions and operational data require the FastAPI backend.")

intake_tab, ops_tab, explorer_tab, api_tab = st.tabs(["Live Intake", "Operations", "Request Review", "API Reference"])

with intake_tab:
    st.subheader("Create Prior Authorization Request")
    left, right = st.columns([0.95, 1.25])

    with left:
        patient_id = st.text_input("Patient ID", value="P-1001")
        payer = st.selectbox("Payer", ["Aetna", "UnitedHealthcare", "Cigna", "Other"])
        procedure_code = st.selectbox("Procedure Code", ["72148", "73721", "29881", "99214"])
        diagnosis_codes = st.text_input("Diagnosis Codes", value="M54.50")
        attached_documents = st.multiselect(
            "Attached Documents",
            DOC_OPTIONS,
            default=["clinical_notes"],
        )
        clinical_note = st.text_area(
            "Clinical Note",
            value="Patient has chronic lumbar pain. Completed 8 weeks physical therapy and NSAIDs with no improvement.",
            height=190,
        )

        payload = build_payload(patient_id, payer, procedure_code, diagnosis_codes, clinical_note, attached_documents)
        create_clicked = st.button("Create Request", type="primary", disabled=not api_available)

        if create_clicked:
            try:
                created = post_json("/requests", payload)
                st.success(f"Request #{created['id']} created with {created['risk_level']} risk.")
                st.session_state["last_created_request_id"] = created["id"]
            except requests.RequestException as exc:
                st.error(f"Request creation failed: {exc}")

    with right:
        st.subheader("Live Predictive Assessment")
        if api_available:
            try:
                preview = post_json("/requests/preview", payload)
                render_preview(preview)
            except requests.RequestException as exc:
                st.error(f"Live preview failed: {exc}")
        else:
            st.info("Start the backend to enable live risk scoring.")

with ops_tab:
    st.subheader("Operational Summary")
    if api_available:
        try:
            summary = get_json("/ops/summary")
            requests_data = get_json("/requests")
            metric_cols = st.columns(5)
            metric_cols[0].metric("Total Requests", summary["total_requests"])
            metric_cols[1].metric("Avg Risk", f"{summary['average_risk_score']:.0%}")
            metric_cols[2].metric("Ready", summary["by_status"].get("ready_to_submit", 0))
            metric_cols[3].metric("Needs Review", summary["by_status"].get("needs_review", 0))
            metric_cols[4].metric("Submitted", summary["by_status"].get("submitted", 0))

            chart_cols = st.columns(2)
            with chart_cols[0]:
                st.subheader("Status Mix")
                status_df = pd.DataFrame(
                    [{"status": key.replace("_", " ").title(), "count": value} for key, value in summary["by_status"].items()]
                )
                if status_df.empty:
                    st.info("No status data yet.")
                else:
                    st.bar_chart(status_df, x="status", y="count", use_container_width=True)
            with chart_cols[1]:
                st.subheader("Risk Mix")
                risk_df = pd.DataFrame(
                    [{"risk_level": key.title(), "count": value} for key, value in summary["by_risk"].items()]
                )
                if risk_df.empty:
                    st.info("No risk data yet.")
                else:
                    st.bar_chart(risk_df, x="risk_level", y="count", use_container_width=True)

            st.subheader("Request Queue")
            st.dataframe(to_request_table(requests_data), use_container_width=True, hide_index=True)
        except requests.RequestException as exc:
            st.error(f"Unable to load operational data: {exc}")
    else:
        st.info("Operational metrics will appear after the backend is running.")

with explorer_tab:
    st.subheader("Review and Submit Packets")
    if api_available:
        try:
            requests_data = get_json("/requests")
            if not requests_data:
                st.info("No requests have been created yet.")
            else:
                labels = {
                    f"#{item['id']} | {item['patient_id']} | {item['payer']} | {item['risk_level'].title()}": item["id"]
                    for item in requests_data
                }
                selected_label = st.selectbox("Select Request", list(labels.keys()))
                selected_id = labels[selected_label]
                detail = get_json(f"/requests/{selected_id}")

                detail_cols = st.columns([0.8, 1.2])
                with detail_cols[0]:
                    st.metric("Denial Risk", f"{detail['denial_risk_score']:.0%}")
                    st.write(f"Status: **{detail['status'].replace('_', ' ').title()}**")
                    st.write(f"Missing documents: {', '.join(detail['missing_documents']) or 'None'}")
                    if st.button("Submit Selected Request", disabled=detail["status"] == "submitted"):
                        submitted = post_json(f"/requests/{selected_id}/submit", {})
                        st.success(f"Request #{selected_id} submission status: {submitted['status']}.")
                with detail_cols[1]:
                    st.json(detail["packet_summary"])
        except requests.RequestException as exc:
            st.error(f"Unable to review requests: {exc}")
    else:
        st.info("Start the backend to review saved requests.")

with api_tab:
    st.subheader("API Endpoints")
    st.write(f"Swagger UI: `{API_BASE_URL}/docs`")
    st.write(f"OpenAPI JSON: `{API_BASE_URL}/openapi.json`")
    endpoint_rows = pd.DataFrame(
        [
            {"method": "GET", "path": "/health", "purpose": "Backend health check"},
            {"method": "POST", "path": "/requests/preview", "purpose": "Real-time risk and readiness preview"},
            {"method": "POST", "path": "/requests", "purpose": "Create a prior authorization request"},
            {"method": "GET", "path": "/requests", "purpose": "List saved requests"},
            {"method": "GET", "path": "/requests/{request_id}", "purpose": "Retrieve request detail"},
            {"method": "POST", "path": "/requests/{request_id}/submit", "purpose": "Submit or block packet"},
            {"method": "GET", "path": "/ops/summary", "purpose": "Operational summary metrics"},
        ]
    )
    st.dataframe(endpoint_rows, use_container_width=True, hide_index=True)
