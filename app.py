import os
from io import StringIO

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
REQUIRED_CSV_COLUMNS = ["patient_id", "payer", "procedure_code", "diagnosis_codes", "clinical_note", "attached_documents"]
OPTIONAL_PATIENT_COLUMNS = ["patient_age", "prior_denials_12m", "chronic_condition_count", "recent_ed_visits_6m", "urgency"]


st.set_page_config(page_title="Prior Auth Copilot", layout="wide")
st.markdown(
    """
    <style>
        .block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
        [data-testid="stMetric"] {
            background: #f8fafc;
            border: 1px solid #dbeafe;
            border-radius: 8px;
            padding: 0.85rem 1rem;
        }
        [data-testid="stSidebar"] {
            background: #eff6ff;
        }
        h1, h2, h3 {color: #0f172a;}
        div[data-testid="stAlert"] {border-radius: 8px;}
    </style>
    """,
    unsafe_allow_html=True,
)


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
    return [code.strip() for code in str(raw_codes).replace(";", ",").split(",") if code.strip()]


def normalize_list_cell(value) -> list[str]:
    if pd.isna(value):
        return []
    return parse_codes(value)


def clean_int(value, default: int = 0) -> int:
    if pd.isna(value) or value == "":
        return default
    return int(float(value))


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


def build_patient_payload(
    auth_payload: dict,
    patient_age: int,
    prior_denials_12m: int,
    chronic_condition_count: int,
    recent_ed_visits_6m: int,
    urgency: str,
) -> dict:
    return {
        **auth_payload,
        "patient_age": patient_age,
        "prior_denials_12m": prior_denials_12m,
        "chronic_condition_count": chronic_condition_count,
        "recent_ed_visits_6m": recent_ed_visits_6m,
        "urgency": urgency,
    }


def payload_from_row(row: pd.Series) -> dict:
    return {
        "patient_id": str(row["patient_id"]).strip(),
        "payer": str(row["payer"]).strip(),
        "procedure_code": str(row["procedure_code"]).strip(),
        "diagnosis_codes": normalize_list_cell(row["diagnosis_codes"]),
        "clinical_note": str(row["clinical_note"]).strip(),
        "attached_documents": normalize_list_cell(row["attached_documents"]),
    }


def patient_payload_from_row(row: pd.Series, auth_payload: dict) -> dict:
    urgency_value = row.get("urgency", "routine")
    if pd.isna(urgency_value):
        urgency = "routine"
    else:
        urgency = str(urgency_value).strip().lower()
    if urgency not in {"routine", "urgent", "emergent"}:
        urgency = "routine"

    return build_patient_payload(
        auth_payload,
        patient_age=clean_int(row.get("patient_age", 45), 45),
        prior_denials_12m=clean_int(row.get("prior_denials_12m", 0), 0),
        chronic_condition_count=clean_int(row.get("chronic_condition_count", 0), 0),
        recent_ed_visits_6m=clean_int(row.get("recent_ed_visits_6m", 0), 0),
        urgency=urgency,
    )


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

    action_cols = st.columns([1.0, 1.0])
    with action_cols[0]:
        st.subheader("Next Best Actions")
        for action in preview["recommended_actions"]:
            st.write(f"- {action}")
        st.subheader("Missing Documents")
        if preview["missing_documents"]:
            st.warning(", ".join(preview["missing_documents"]))
        else:
            st.success("No required documents are missing.")

    with action_cols[1]:
        st.subheader("Extracted Clinical Signals")
        signals = preview["extracted_signals"]
        st.write(f"Matched signals: {', '.join(signals.get('matched_signals', [])) or 'None'}")
        st.write(f"Medical necessity narrative: {'Yes' if signals.get('has_medical_necessity_narrative') else 'No'}")
        st.write(f"Conservative treatment documented: {'Yes' if signals.get('conservative_treatment_documented') else 'No'}")
        st.write(f"Clinical note length: {signals.get('note_length', 0)} characters")


def render_patient_preview(patient_preview: dict):
    friction_score = float(patient_preview["predicted_prior_auth_friction"])
    complexity_score = float(patient_preview["patient_complexity_score"])
    metric_cols = st.columns(3)
    metric_cols[0].metric("Prior Auth Friction", f"{friction_score:.0%}")
    metric_cols[1].metric("Patient Complexity", f"{complexity_score:.0%}")
    metric_cols[2].metric("Complexity Level", patient_preview["complexity_level"].title())
    st.progress(friction_score)

    detail_cols = st.columns([0.9, 1.1])
    with detail_cols[0]:
        st.subheader("Key Drivers")
        if patient_preview["drivers"]:
            st.write(", ".join(driver.replace("_", " ").title() for driver in patient_preview["drivers"]))
        else:
            st.write("No major patient-level drivers detected.")
    with detail_cols[1]:
        st.subheader("Clinical Review Actions")
        for action in patient_preview["recommended_actions"]:
            st.write(f"- {action}")


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


def filter_requests(
    records: list[dict],
    search_term: str,
    statuses: list[str],
    risk_levels: list[str],
    min_risk_score: float,
) -> list[dict]:
    term = search_term.strip().lower()
    filtered = []
    for item in records:
        searchable = " ".join(
            [
                str(item.get("patient_id", "")),
                str(item.get("payer", "")),
                str(item.get("procedure_code", "")),
                str(item.get("status", "")),
                str(item.get("risk_level", "")),
                " ".join(item.get("diagnosis_codes", []) or []),
            ]
        ).lower()
        if term and term not in searchable:
            continue
        if statuses and item.get("status") not in statuses:
            continue
        if risk_levels and item.get("risk_level") not in risk_levels:
            continue
        if float(item.get("denial_risk_score", 0) or 0) < min_risk_score:
            continue
        filtered.append(item)
    return filtered


def to_patient_explorer_table(records: list[dict]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()
    df = to_request_table(records)
    if "missing_documents" in df.columns:
        df["missing_documents"] = df["missing_documents"].apply(lambda value: ", ".join(value) if isinstance(value, list) else value)
    return df


def auth_payload_from_record(record: dict) -> dict:
    return {
        "patient_id": record["patient_id"],
        "payer": record["payer"],
        "procedure_code": record["procedure_code"],
        "diagnosis_codes": record.get("diagnosis_codes", []),
        "clinical_note": record["clinical_note"],
        "attached_documents": record.get("attached_documents", []),
    }


def sample_csv() -> str:
    sample = pd.DataFrame(
        [
            {
                "patient_id": "P-1001",
                "payer": "Aetna",
                "procedure_code": "72148",
                "diagnosis_codes": "M54.50",
                "clinical_note": "Patient has chronic lumbar pain. Completed 8 weeks physical therapy and NSAIDs with no improvement.",
                "attached_documents": "clinical_notes;xray_report",
                "patient_age": 67,
                "prior_denials_12m": 1,
                "chronic_condition_count": 3,
                "recent_ed_visits_6m": 1,
                "urgency": "routine",
            },
            {
                "patient_id": "P-1002",
                "payer": "Cigna",
                "procedure_code": "29881",
                "diagnosis_codes": "S83.241A",
                "clinical_note": "Knee pain with failed conservative care. MRI reviewed and operative plan attached.",
                "attached_documents": "clinical_notes;imaging_report;operative_plan",
                "patient_age": 54,
                "prior_denials_12m": 0,
                "chronic_condition_count": 1,
                "recent_ed_visits_6m": 0,
                "urgency": "routine",
            },
        ]
    )
    return sample.to_csv(index=False)


def analyze_bulk_rows(df: pd.DataFrame, limit: int) -> tuple[pd.DataFrame, list[dict]]:
    rows = []
    payloads = []
    for index, row in df.head(limit).iterrows():
        auth_payload = payload_from_row(row)
        patient_payload = patient_payload_from_row(row, auth_payload)
        try:
            auth_preview = post_json("/requests/preview", auth_payload)
            patient_preview = post_json("/patients/risk-preview", patient_payload)
            rows.append(
                {
                    "row": index + 1,
                    "patient_id": auth_payload["patient_id"],
                    "payer": auth_payload["payer"],
                    "procedure_code": auth_payload["procedure_code"],
                    "denial_risk_score": auth_preview["denial_risk_score"],
                    "risk_level": auth_preview["risk_level"],
                    "patient_friction_score": patient_preview["predicted_prior_auth_friction"],
                    "patient_complexity_level": patient_preview["complexity_level"],
                    "status": auth_preview["status"],
                    "missing_documents": ", ".join(auth_preview["missing_documents"]),
                    "recommended_action": patient_preview["recommended_actions"][0],
                    "api_status": "ok",
                }
            )
            payloads.append(auth_payload)
        except (requests.RequestException, ValueError, KeyError) as exc:
            rows.append(
                {
                    "row": index + 1,
                    "patient_id": str(row.get("patient_id", "")),
                    "payer": str(row.get("payer", "")),
                    "procedure_code": str(row.get("procedure_code", "")),
                    "denial_risk_score": None,
                    "risk_level": "error",
                    "patient_friction_score": None,
                    "patient_complexity_level": "error",
                    "status": "error",
                    "missing_documents": "",
                    "recommended_action": str(exc),
                    "api_status": "error",
                }
            )
    return pd.DataFrame(rows), payloads


st.title("Prior Auth Copilot")
st.caption("Prior authorization intake, real-time denial-risk prediction, patient-level friction review, and packet readiness operations.")

api_available = api_is_available()
sidebar_summary = None
with st.sidebar:
    st.title("Prior Auth Control Center")
    st.caption("Worklist filters, backend health, and intake guidance.")

    st.subheader("Backend")
    st.code(API_BASE_URL)
    if api_available:
        st.success("FastAPI backend is healthy.")
        try:
            sidebar_summary = get_json("/ops/summary")
            st.metric("Total Requests", sidebar_summary["total_requests"])
            st.metric("Average Denial Risk", f"{sidebar_summary['average_risk_score']:.0%}")
        except requests.RequestException:
            st.info("Backend is online, but summary metrics are temporarily unavailable.")
    else:
        st.error("FastAPI backend is offline.")
        st.code("uvicorn prior_auth_copilot.api.main:app --reload --port 8000")

    if st.button("Refresh Dashboard"):
        st.rerun()

    st.divider()
    st.subheader("Worklist Filters")
    sidebar_search = st.text_input("Search Queue", placeholder="Patient, payer, CPT, status")
    sidebar_statuses = st.multiselect(
        "Status",
        ["ready_to_submit", "needs_review", "submitted", "blocked_missing_documents"],
        default=[],
        format_func=lambda value: value.replace("_", " ").title(),
    )
    sidebar_risk_levels = st.multiselect(
        "Risk Level",
        ["low", "medium", "high"],
        default=[],
        format_func=lambda value: value.title(),
    )
    sidebar_min_risk = st.slider("Minimum Denial Risk", min_value=0.0, max_value=1.0, value=0.0, step=0.05)

    st.divider()
    with st.expander("CSV Intake Format"):
        st.write("Required columns:")
        st.write(", ".join(REQUIRED_CSV_COLUMNS))
        st.write("Optional patient context:")
        st.write(", ".join(OPTIONAL_PATIENT_COLUMNS))
        st.download_button(
            "Download Sample",
            data=sample_csv(),
            file_name="prior_auth_bulk_sample.csv",
            mime="text/csv",
            key="sidebar_sample_csv",
        )

    with st.expander("Model Signals"):
        st.write("Packet risk uses payer rules, missing documents, medical-necessity cues, and conservative-treatment evidence.")
        st.write("Patient friction adds age, recent denials, chronic complexity, recent ED use, urgency, and packet gaps.")

if not api_available:
    st.warning("The dashboard is running, but live predictions and operational data require the FastAPI backend.")

intake_tab, batch_tab, patient_tab, ops_tab, explorer_tab, api_tab = st.tabs(
    ["Live Intake", "Bulk CSV Intake", "Patient Explorer", "Operations", "Request Review", "API Reference"]
)

with intake_tab:
    st.subheader("Single Request Intake")
    left, right = st.columns([0.9, 1.25])

    with left:
        patient_id = st.text_input("Patient ID", value="P-1001")
        payer = st.selectbox("Payer", ["Aetna", "UnitedHealthcare", "Cigna", "Other"])
        procedure_code = st.selectbox("Procedure Code", ["72148", "73721", "29881", "99214"])
        diagnosis_codes = st.text_input("Diagnosis Codes", value="M54.50")
        attached_documents = st.multiselect("Attached Documents", DOC_OPTIONS, default=["clinical_notes"])
        clinical_note = st.text_area(
            "Clinical Note",
            value="Patient has chronic lumbar pain. Completed 8 weeks physical therapy and NSAIDs with no improvement.",
            height=170,
        )

        st.subheader("Patient Context")
        patient_age = st.number_input("Age", min_value=0, max_value=120, value=67, step=1)
        prior_denials_12m = st.number_input("Prior Denials, Last 12 Months", min_value=0, max_value=50, value=1, step=1)
        chronic_condition_count = st.number_input("Chronic Condition Count", min_value=0, max_value=30, value=3, step=1)
        recent_ed_visits_6m = st.number_input("ED Visits, Last 6 Months", min_value=0, max_value=50, value=1, step=1)
        urgency = st.selectbox("Request Urgency", ["routine", "urgent", "emergent"])

        payload = build_payload(patient_id, payer, procedure_code, diagnosis_codes, clinical_note, attached_documents)
        patient_payload = build_patient_payload(
            payload,
            patient_age,
            prior_denials_12m,
            chronic_condition_count,
            recent_ed_visits_6m,
            urgency,
        )
        create_clicked = st.button("Create Request", type="primary", disabled=not api_available)

        if create_clicked:
            try:
                created = post_json("/requests", payload)
                st.success(f"Request #{created['id']} created with {created['risk_level']} risk.")
                st.session_state["last_created_request_id"] = created["id"]
            except requests.RequestException as exc:
                st.error(f"Request creation failed: {exc}")

    with right:
        st.subheader("Live Authorization Assessment")
        if api_available:
            try:
                preview = post_json("/requests/preview", payload)
                render_preview(preview)
                st.divider()
                st.subheader("Patient-Level Predictive Assessment")
                patient_preview = post_json("/patients/risk-preview", patient_payload)
                render_patient_preview(patient_preview)
            except requests.RequestException as exc:
                st.error(f"Live preview failed: {exc}")
        else:
            st.info("Start the backend to enable live risk scoring.")

with batch_tab:
    st.subheader("Bulk Patient CSV Intake")
    st.download_button(
        "Download Sample CSV",
        data=sample_csv(),
        file_name="prior_auth_bulk_sample.csv",
        mime="text/csv",
    )
    uploaded_file = st.file_uploader("Upload Prior Authorization CSV", type=["csv"])

    if uploaded_file is not None:
        raw_text = uploaded_file.getvalue().decode("utf-8")
        uploaded_df = pd.read_csv(StringIO(raw_text))
        if uploaded_df.empty:
            st.warning("The uploaded CSV has headers but no rows to analyze.")
        else:
            st.dataframe(uploaded_df.head(25), use_container_width=True, hide_index=True)

        missing_columns = [column for column in REQUIRED_CSV_COLUMNS if column not in uploaded_df.columns]
        if missing_columns:
            st.error(f"Missing required column(s): {', '.join(missing_columns)}")
        elif uploaded_df.empty:
            st.info("Add at least one patient row before running analysis.")
        elif not api_available:
            st.info("Start the backend to analyze and create uploaded rows.")
        else:
            row_limit = st.slider("Rows To Analyze", min_value=1, max_value=len(uploaded_df), value=min(25, len(uploaded_df)))
            if st.button("Analyze Uploaded Rows"):
                with st.spinner("Scoring uploaded rows..."):
                    bulk_preview_df, bulk_payloads = analyze_bulk_rows(uploaded_df, row_limit)
                st.session_state["bulk_preview_df"] = bulk_preview_df
                st.session_state["bulk_payloads"] = bulk_payloads

            if "bulk_preview_df" in st.session_state:
                preview_df = st.session_state["bulk_preview_df"]
                st.subheader("Bulk Risk Preview")
                st.dataframe(preview_df, use_container_width=True, hide_index=True)
                st.download_button(
                    "Download Risk Preview",
                    data=preview_df.to_csv(index=False),
                    file_name="prior_auth_bulk_risk_preview.csv",
                    mime="text/csv",
                )

                if st.button("Create Requests From Analyzed Rows", type="primary"):
                    created = 0
                    failed = 0
                    for row_payload in st.session_state.get("bulk_payloads", []):
                        try:
                            post_json("/requests", row_payload)
                            created += 1
                        except requests.RequestException:
                            failed += 1
                    st.success(f"Created {created} request(s). Failed rows: {failed}.")

with patient_tab:
    st.subheader("Patient Explorer")
    if api_available:
        try:
            requests_data = get_json("/requests")
            patient_search = st.text_input(
                "Search Patients",
                value=sidebar_search,
                placeholder="Search by patient ID, payer, CPT, diagnosis, risk, or status",
                key="patient_explorer_search",
            )
            filtered_requests = filter_requests(
                requests_data,
                patient_search,
                sidebar_statuses,
                sidebar_risk_levels,
                sidebar_min_risk,
            )

            if not filtered_requests:
                st.info("No saved patient requests match the current search and sidebar filters.")
            else:
                st.caption(f"Showing {len(filtered_requests)} of {len(requests_data)} saved request(s).")
                st.dataframe(to_patient_explorer_table(filtered_requests), use_container_width=True, hide_index=True)

                request_options = {
                    f"#{item['id']} | {item['patient_id']} | {item['payer']} | {item['procedure_code']} | {item['risk_level'].title()}": item
                    for item in filtered_requests
                }
                selected_request_label = st.selectbox("Open Patient Request", list(request_options.keys()))
                selected_request = request_options[selected_request_label]
                request_detail = get_json(f"/requests/{selected_request['id']}")

                st.divider()
                left, right = st.columns([0.9, 1.15])
                with left:
                    st.subheader("Patient Context Scenario")
                    explorer_age = st.number_input("Age", min_value=0, max_value=120, value=67, step=1, key="explorer_age")
                    explorer_prior_denials = st.number_input(
                        "Prior Denials, Last 12 Months",
                        min_value=0,
                        max_value=50,
                        value=1,
                        step=1,
                        key="explorer_prior_denials",
                    )
                    explorer_chronic_count = st.number_input(
                        "Chronic Condition Count",
                        min_value=0,
                        max_value=30,
                        value=3,
                        step=1,
                        key="explorer_chronic_count",
                    )
                    explorer_ed_visits = st.number_input(
                        "ED Visits, Last 6 Months",
                        min_value=0,
                        max_value=50,
                        value=1,
                        step=1,
                        key="explorer_ed_visits",
                    )
                    explorer_urgency = st.selectbox(
                        "Urgency",
                        ["routine", "urgent", "emergent"],
                        key="explorer_urgency",
                    )
                    st.write(f"Saved request status: **{request_detail['status'].replace('_', ' ').title()}**")
                    st.write(f"Attached documents: {', '.join(request_detail['attached_documents']) or 'None'}")
                    st.write(f"Missing documents: {', '.join(request_detail['missing_documents']) or 'None'}")

                with right:
                    st.subheader("Predictive Results")
                    auth_payload = auth_payload_from_record(request_detail)
                    patient_payload = build_patient_payload(
                        auth_payload,
                        explorer_age,
                        explorer_prior_denials,
                        explorer_chronic_count,
                        explorer_ed_visits,
                        explorer_urgency,
                    )
                    patient_preview = post_json("/patients/risk-preview", patient_payload)
                    render_patient_preview(patient_preview)

                with st.expander("Score Current Search Results"):
                    st.write("Applies the patient-context scenario above to the current filtered request list.")
                    score_limit = st.slider(
                        "Rows To Score",
                        min_value=1,
                        max_value=len(filtered_requests),
                        value=min(25, len(filtered_requests)),
                        key="patient_score_limit",
                    )
                    if st.button("Score Filtered Patients"):
                        scored_rows = []
                        for item in filtered_requests[:score_limit]:
                            detail = get_json(f"/requests/{item['id']}")
                            scenario_payload = build_patient_payload(
                                auth_payload_from_record(detail),
                                explorer_age,
                                explorer_prior_denials,
                                explorer_chronic_count,
                                explorer_ed_visits,
                                explorer_urgency,
                            )
                            score = post_json("/patients/risk-preview", scenario_payload)
                            scored_rows.append(
                                {
                                    "request_id": item["id"],
                                    "patient_id": score["patient_id"],
                                    "payer": detail["payer"],
                                    "procedure_code": detail["procedure_code"],
                                    "authorization_risk": score["authorization_risk_score"],
                                    "patient_friction": score["predicted_prior_auth_friction"],
                                    "complexity_level": score["complexity_level"],
                                    "top_action": score["recommended_actions"][0],
                                }
                            )
                        scored_df = pd.DataFrame(scored_rows)
                        st.session_state["patient_explorer_scores"] = scored_df

                    if "patient_explorer_scores" in st.session_state:
                        scored_df = st.session_state["patient_explorer_scores"]
                        st.dataframe(scored_df, use_container_width=True, hide_index=True)
                        st.download_button(
                            "Download Patient Scores",
                            data=scored_df.to_csv(index=False),
                            file_name="patient_predictive_results.csv",
                            mime="text/csv",
                        )
        except requests.RequestException as exc:
            st.error(f"Unable to explore patients: {exc}")
    else:
        st.info("Start the backend to search patients and compute predictive results.")

with ops_tab:
    st.subheader("Operational Summary")
    if api_available:
        try:
            summary = get_json("/ops/summary")
            requests_data = get_json("/requests")
            filtered_requests = filter_requests(
                requests_data,
                sidebar_search,
                sidebar_statuses,
                sidebar_risk_levels,
                sidebar_min_risk,
            )
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
            st.caption(f"Showing {len(filtered_requests)} of {len(requests_data)} request(s) after sidebar filters.")
            st.dataframe(to_request_table(filtered_requests), use_container_width=True, hide_index=True)
        except requests.RequestException as exc:
            st.error(f"Unable to load operational data: {exc}")
    else:
        st.info("Operational metrics will appear after the backend is running.")

with explorer_tab:
    st.subheader("Review and Submit Packets")
    if api_available:
        try:
            requests_data = get_json("/requests")
            filtered_requests = filter_requests(
                requests_data,
                sidebar_search,
                sidebar_statuses,
                sidebar_risk_levels,
                sidebar_min_risk,
            )
            if not requests_data:
                st.info("No requests have been created yet.")
            elif not filtered_requests:
                st.info("No requests match the active sidebar filters.")
            else:
                labels = {
                    f"#{item['id']} | {item['patient_id']} | {item['payer']} | {item['risk_level'].title()}": item["id"]
                    for item in filtered_requests
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
            {"method": "POST", "path": "/requests/preview", "purpose": "Real-time packet risk and readiness preview"},
            {"method": "POST", "path": "/patients/risk-preview", "purpose": "Patient-level prior authorization friction preview"},
            {"method": "POST", "path": "/requests", "purpose": "Create a prior authorization request"},
            {"method": "GET", "path": "/requests", "purpose": "List saved requests"},
            {"method": "GET", "path": "/requests/{request_id}", "purpose": "Retrieve request detail"},
            {"method": "POST", "path": "/requests/{request_id}/submit", "purpose": "Submit or block packet"},
            {"method": "GET", "path": "/ops/summary", "purpose": "Operational summary metrics"},
        ]
    )
    st.dataframe(endpoint_rows, use_container_width=True, hide_index=True)
