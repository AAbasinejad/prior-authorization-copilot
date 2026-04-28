from fastapi.testclient import TestClient
from prior_auth_copilot.api.main import app


client = TestClient(app)


def demo_payload():
    return {
        "patient_id": "P-2001",
        "payer": "Aetna",
        "procedure_code": "72148",
        "diagnosis_codes": ["M54.50"],
        "clinical_note": "Patient has chronic lumbar pain. Completed 8 weeks physical therapy and NSAIDs with no improvement.",
        "attached_documents": ["clinical_notes"],
    }


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_preview_request_without_persisting():
    preview = client.post("/requests/preview", json=demo_payload())
    assert preview.status_code == 200
    body = preview.json()
    assert body["risk_level"] in {"low", "medium", "high"}
    assert body["status"] in {"ready_to_submit", "needs_review"}
    assert "recommended_actions" in body
    assert "ready_to_submit" in body


def test_patient_level_risk_preview():
    payload = {
        **demo_payload(),
        "patient_age": 67,
        "prior_denials_12m": 1,
        "chronic_condition_count": 3,
        "recent_ed_visits_6m": 1,
        "urgency": "routine",
    }
    preview = client.post("/patients/risk-preview", json=payload)
    assert preview.status_code == 200
    body = preview.json()
    assert body["complexity_level"] in {"low", "medium", "high"}
    assert 0 <= body["predicted_prior_auth_friction"] <= 1
    assert body["recommended_actions"]


def test_create_and_submit_request():
    payload = demo_payload()
    created = client.post("/requests", json=payload)
    assert created.status_code == 200
    body = created.json()
    assert body["risk_level"] in {"low", "medium", "high"}
    assert body["packet_summary"]["recommended_actions"]
    submit = client.post(f"/requests/{body['id']}/submit")
    assert submit.status_code == 200
    assert submit.json()["status"] in {"submitted", "blocked_missing_documents"}


def test_openapi_uses_readable_examples():
    schema = client.get("/openapi.json").json()
    request_schema = schema["components"]["schemas"]["PriorAuthRequestCreate"]
    assert request_schema["examples"][0]["patient_id"] == "P-1001"
