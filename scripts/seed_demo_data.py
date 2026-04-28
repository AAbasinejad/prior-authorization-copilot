from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from prior_auth_copilot.core.database import Base, SessionLocal, engine
from prior_auth_copilot.models.schemas import PriorAuthRequestCreate
from prior_auth_copilot.repositories.prior_auth_repository import PriorAuthRepository
from prior_auth_copilot.services.workflow import build_request_payload


Base.metadata.create_all(bind=engine)
examples = [
    PriorAuthRequestCreate(patient_id="P-1001", payer="Aetna", procedure_code="72148", diagnosis_codes=["M54.50"], clinical_note="Patient has chronic lumbar pain. Completed 8 weeks physical therapy and NSAIDs with no improvement.", attached_documents=["clinical_notes"]),
    PriorAuthRequestCreate(patient_id="P-1002", payer="Cigna", procedure_code="29881", diagnosis_codes=["S83.206A"], clinical_note="Persistent meniscal symptoms, locking, worsening pain, failed conservative management.", attached_documents=["clinical_notes", "operative_plan"]),
]
db = SessionLocal(); repo = PriorAuthRepository(db)
for req in examples:
    repo.create(build_request_payload(req))
db.close(); print("Demo data seeded.")
