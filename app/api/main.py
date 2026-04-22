from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from app.core.database import Base, engine, get_db
from app.models.schemas import OpsSummary, PriorAuthRequestCreate, PriorAuthRequestResponse, SubmissionResponse
from app.repositories.prior_auth import PriorAuthRepository
from app.services.workflow import build_request_payload, build_submission_packet


Base.metadata.create_all(bind=engine)
app = FastAPI(title="Prior Auth Copilot", version="1.0.0")


@app.get("/health")
def healthcheck():
    return {"status": "ok"}


@app.post("/requests", response_model=PriorAuthRequestResponse)
def create_request(request: PriorAuthRequestCreate, db: Session = Depends(get_db)):
    return PriorAuthRepository(db).create(build_request_payload(request))


@app.get("/requests", response_model=list[PriorAuthRequestResponse])
def list_requests(db: Session = Depends(get_db)):
    return PriorAuthRepository(db).list()


@app.get("/requests/{request_id}", response_model=PriorAuthRequestResponse)
def get_request(request_id: int, db: Session = Depends(get_db)):
    item = PriorAuthRepository(db).get(request_id)
    if not item:
        raise HTTPException(status_code=404, detail="Request not found")
    return item


@app.post("/requests/{request_id}/submit", response_model=SubmissionResponse)
def submit_request(request_id: int, db: Session = Depends(get_db)):
    repo = PriorAuthRepository(db)
    item = repo.get(request_id)
    if not item:
        raise HTTPException(status_code=404, detail="Request not found")
    packet = build_submission_packet(item)
    status = "submitted" if packet["ready"] else "blocked_missing_documents"
    repo.update(item, {"status": status, "packet_summary": packet})
    return {"request_id": request_id, "status": status, "submitted_packet": packet}


@app.get("/ops/summary", response_model=OpsSummary)
def ops_summary(db: Session = Depends(get_db)):
    return PriorAuthRepository(db).summary()
