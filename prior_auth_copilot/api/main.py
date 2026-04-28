from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from prior_auth_copilot.core.database import Base, engine, get_db
from prior_auth_copilot.models.schemas import (
    HealthResponse,
    OpsSummary,
    PatientRiskPreviewRequest,
    PatientRiskPreviewResponse,
    PriorAuthPreviewResponse,
    PriorAuthRequestCreate,
    PriorAuthRequestResponse,
    SubmissionResponse,
)
from prior_auth_copilot.repositories.prior_auth_repository import PriorAuthRepository
from prior_auth_copilot.services.patient_risk import score_patient_prior_auth_friction
from prior_auth_copilot.services.workflow import build_preview_response, build_request_payload, build_submission_packet


Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="Prior Auth Copilot",
    version="1.1.0",
    description=(
        "Decision-support API for prior authorization intake, payer-rule checks, denial-risk scoring, "
        "packet readiness, and operational monitoring."
    ),
)


@app.get("/health", response_model=HealthResponse, tags=["System"], summary="Check API health")
def health_check():
    return {"status": "ok"}


@app.post(
    "/requests/preview",
    response_model=PriorAuthPreviewResponse,
    tags=["Prior Authorization"],
    summary="Preview denial risk and packet readiness without saving",
)
def preview_request(request: PriorAuthRequestCreate):
    return build_preview_response(request)


@app.post(
    "/patients/risk-preview",
    response_model=PatientRiskPreviewResponse,
    tags=["Clinical Risk"],
    summary="Preview patient-level prior authorization friction",
)
def preview_patient_risk(request: PatientRiskPreviewRequest):
    return score_patient_prior_auth_friction(request)


@app.post(
    "/requests",
    response_model=PriorAuthRequestResponse,
    tags=["Prior Authorization"],
    summary="Create a prior authorization request",
)
def create_request(request: PriorAuthRequestCreate, db: Session = Depends(get_db)):
    return PriorAuthRepository(db).create(build_request_payload(request))


@app.get(
    "/requests",
    response_model=list[PriorAuthRequestResponse],
    tags=["Prior Authorization"],
    summary="List prior authorization requests",
)
def list_requests(db: Session = Depends(get_db)):
    return PriorAuthRepository(db).list()


@app.get(
    "/requests/{request_id}",
    response_model=PriorAuthRequestResponse,
    tags=["Prior Authorization"],
    summary="Get a prior authorization request by ID",
)
def get_request(request_id: int, db: Session = Depends(get_db)):
    item = PriorAuthRepository(db).get(request_id)
    if not item:
        raise HTTPException(status_code=404, detail="Request not found")
    return item


@app.post(
    "/requests/{request_id}/submit",
    response_model=SubmissionResponse,
    tags=["Prior Authorization"],
    summary="Submit a request packet when documentation is complete",
)
def submit_request(request_id: int, db: Session = Depends(get_db)):
    repo = PriorAuthRepository(db)
    item = repo.get(request_id)
    if not item:
        raise HTTPException(status_code=404, detail="Request not found")
    packet = build_submission_packet(item)
    status = "submitted" if packet["ready"] else "blocked_missing_documents"
    repo.update(item, {"status": status, "packet_summary": packet})
    return {"request_id": request_id, "status": status, "submitted_packet": packet}


@app.get("/ops/summary", response_model=OpsSummary, tags=["Operations"], summary="Get operational request summary")
def ops_summary(db: Session = Depends(get_db)):
    return PriorAuthRepository(db).summary()
