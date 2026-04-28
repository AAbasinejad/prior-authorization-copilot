from sqlalchemy import func
from sqlalchemy.orm import Session
from prior_auth_copilot.models.database_models import PriorAuthRequestDB


class PriorAuthRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payload: dict) -> PriorAuthRequestDB:
        obj = PriorAuthRequestDB(**payload)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get(self, request_id: int) -> PriorAuthRequestDB | None:
        return self.db.query(PriorAuthRequestDB).filter(PriorAuthRequestDB.id == request_id).first()

    def list(self) -> list[PriorAuthRequestDB]:
        return self.db.query(PriorAuthRequestDB).order_by(PriorAuthRequestDB.created_at.desc()).all()

    def update(self, obj: PriorAuthRequestDB, data: dict) -> PriorAuthRequestDB:
        for key, value in data.items():
            setattr(obj, key, value)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def summary(self) -> dict:
        total = self.db.query(func.count(PriorAuthRequestDB.id)).scalar() or 0
        status_rows = self.db.query(PriorAuthRequestDB.status, func.count(PriorAuthRequestDB.id)).group_by(PriorAuthRequestDB.status).all()
        risk_rows = self.db.query(PriorAuthRequestDB.risk_level, func.count(PriorAuthRequestDB.id)).group_by(PriorAuthRequestDB.risk_level).all()
        avg_risk = self.db.query(func.avg(PriorAuthRequestDB.denial_risk_score)).scalar() or 0.0
        return {"total_requests": total, "by_status": {k: v for k, v in status_rows}, "by_risk": {k: v for k, v in risk_rows}, "average_risk_score": round(float(avg_risk), 4)}
