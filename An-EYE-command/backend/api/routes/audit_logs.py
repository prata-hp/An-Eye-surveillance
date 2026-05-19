from typing import Optional

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.database.session import get_db
from backend.models.incident_model import IncidentModel
from backend.models.audit_log_model import AuditLogModel


router = APIRouter()


@router.get("/audit-logs")
async def get_audit_logs(
    incident_id: Optional[str] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(AuditLogModel)

    if incident_id:
        incident = (
            db.query(IncidentModel)
            .filter(IncidentModel.incident_id == incident_id)
            .first()
        )

        if incident and current_user.get("role") != "Admin" and incident.city != current_user.get("city"):
            return []

        query = query.filter(AuditLogModel.incident_id == incident_id)

    return query.order_by(AuditLogModel.id.desc()).all()
