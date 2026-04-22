from app.core.database import Base, SessionLocal, engine
from app.models.schemas import PriorAuthRequestCreate
from app.repositories.prior_auth import PriorAuthRepository
from app.services.workflow import build_request_payload


Base.metadata.create_all(bind=engine)
examples = [
    PriorAuthRequestCreate(patient_id="P-1001", payer="Aetna", procedure_code="72148", diagnosis_codes=["M54.50"], clinical_note="Patient has chronic lumbar pain. Completed 8 weeks physical therapy and NSAIDs with no improvement.", attached_documents=["clinical_notes"]),
    PriorAuthRequestCreate(patient_id="P-1002", payer="Cigna", procedure_code="29881", diagnosis_codes=["S83.206A"], clinical_note="Persistent meniscal symptoms, locking, worsening pain, failed conservative management.", attached_documents=["clinical_notes", "operative_plan"]),
]
db = SessionLocal(); repo = PriorAuthRepository(db)
for req in examples:
    repo.create(build_request_payload(req))
db.close(); print("Demo data seeded.")
