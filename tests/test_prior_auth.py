from fastapi.testclient import TestClient
from app.api.main import app


client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_create_and_submit_request():
    payload = {
        "patient_id": "P-2001",
        "payer": "Aetna",
        "procedure_code": "72148",
        "diagnosis_codes": ["M54.50"],
        "clinical_note": "Patient has chronic lumbar pain. Completed 8 weeks physical therapy and NSAIDs with no improvement.",
        "attached_documents": ["clinical_notes"],
    }
    created = client.post("/requests", json=payload)
    assert created.status_code == 200
    body = created.json()
    assert body["risk_level"] in {"low", "medium", "high"}
    submit = client.post(f"/requests/{body['id']}/submit")
    assert submit.status_code == 200
    assert submit.json()["status"] in {"submitted", "blocked_missing_documents"}
