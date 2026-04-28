# Prior Authorization Copilot

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-Validation-E92063?logo=pydantic&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-ORM-D71F00?logo=sqlalchemy&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Local_DB-003B57?logo=sqlite&logoColor=white)
![Pytest](https://img.shields.io/badge/Pytest-Tested-0A9EDC?logo=pytest&logoColor=white)

Prior Authorization Copilot is a lightweight prior authorization operations app built with FastAPI and Streamlit. It turns intake details, clinical notes, attached documents, and patient context into packet-readiness checks, denial-risk estimates, patient-level friction scores, and review actions.

The goal is to demonstrate the shape of a real prior-auth workflow: intake a request, extract evidence from the note, apply payer/procedure documentation rules, identify missing documents, score risk before submission, and track work through an operations queue.

## Core Features

- FastAPI service for request intake, preview scoring, submission, and operations summaries.
- Streamlit dashboard with a light theme and a sidebar control center for backend health, queue filters, sample CSV download, and model signal notes.
- Real-time denial-risk preview before a request is saved.
- Patient-level predictive scoring based on age, prior denials, chronic-condition count, recent ED utilization, urgency, and packet gaps.
- Bulk CSV upload for batch preview, scored result export, and bulk request creation.
- Patient Explorer tab for searching saved patients, opening their request history, and recomputing predictive results under different clinical-context scenarios.
- Swagger/OpenAPI examples with realistic request and response values.

## Dashboard

The Streamlit app is organized around the work an authorization team would actually perform:

- **Live Intake**: create a single authorization request and see live packet and patient-level predictions.
- **Bulk CSV Intake**: upload patient/request rows, score them, export results, and create valid requests.
- **Patient Explorer**: search patients or requests, review saved risk context, and rescore selected patients with scenario inputs.
- **Operations**: monitor total volume, average risk, status mix, risk mix, and the active queue.
- **Request Review**: inspect packet summaries and submit requests when documentation is complete.
- **API Reference**: view available backend endpoints and Swagger/OpenAPI links.

The light dashboard theme is configured in `.streamlit/config.toml`.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | API health check |
| `POST` | `/requests/preview` | Real-time packet risk and readiness preview |
| `POST` | `/patients/risk-preview` | Patient-level prior authorization friction preview |
| `POST` | `/requests` | Create a prior authorization request |
| `GET` | `/requests` | List saved requests |
| `GET` | `/requests/{request_id}` | Retrieve request detail |
| `POST` | `/requests/{request_id}/submit` | Submit or block a request packet |
| `GET` | `/ops/summary` | Operational summary metrics |

## Input Format

Single request payload:

```json
{
  "patient_id": "P-1001",
  "payer": "Aetna",
  "procedure_code": "72148",
  "diagnosis_codes": ["M54.50"],
  "clinical_note": "Patient has chronic lumbar pain. Completed 8 weeks physical therapy and NSAIDs with no improvement.",
  "attached_documents": ["clinical_notes", "xray_report"]
}
```

Bulk CSV uploads require:

| Column | Description | Example |
|---|---|---|
| `patient_id` | Internal patient or encounter ID | `P-1001` |
| `payer` | Payer used for rule matching | `Aetna` |
| `procedure_code` | CPT/HCPCS procedure code | `72148` |
| `diagnosis_codes` | Comma- or semicolon-separated ICD codes | `M54.50;M51.36` |
| `clinical_note` | Clinical narrative for signal extraction | `Completed 8 weeks PT with no improvement.` |
| `attached_documents` | Comma- or semicolon-separated document keys | `clinical_notes;xray_report` |

Optional CSV columns for patient-level prediction:

| Column | Example |
|---|---|
| `patient_age` | `67` |
| `prior_denials_12m` | `1` |
| `chronic_condition_count` | `3` |
| `recent_ed_visits_6m` | `1` |
| `urgency` | `routine`, `urgent`, or `emergent` |

## Run Locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn prior_auth_copilot.api.main:app --reload --port 8000
```

Open Swagger at:

```text
http://localhost:8000/docs
```

Start the dashboard in another terminal:

```bash
source .venv/bin/activate
streamlit run app.py
```

Optional demo data:

```bash
python scripts/seed_demo_data.py
```

## Test

```bash
pytest -q
```

The tests cover API health, live request preview, patient-level risk preview, request creation/submission, and OpenAPI example quality.

## Notes

This project is a demo-grade decision-support workflow, not a production clinical authorization engine. The scoring logic is intentionally transparent and rules-based. A production implementation would require payer policy ingestion, audit trails, document OCR, PHI controls, historical-denial calibration, and human-in-the-loop clinical review.
