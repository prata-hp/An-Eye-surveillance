from typing import Optional

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.auth.roles import require_role
from backend.database.session import get_db
from backend.models.incident_model import IncidentModel
from backend.schemas.incident import Incident
from backend.services.audit_logger import log_action
from backend.websocket.manager import manager


router = APIRouter()

VALID_STATUSES = {
    "NEW",
    "UNDER_REVIEW",
    "PENDING",
    "ESCALATED",
    "FALSE_POSITIVE",
    "RESOLVED",
}

ALLOWED_STATUS_TRANSITIONS = {
    "NEW": {"UNDER_REVIEW", "PENDING", "ESCALATED", "FALSE_POSITIVE"},
    "UNDER_REVIEW": {"PENDING", "ESCALATED", "FALSE_POSITIVE"},
    "PENDING": {"UNDER_REVIEW", "ESCALATED", "FALSE_POSITIVE"},
    "ESCALATED": {"RESOLVED"},
    "FALSE_POSITIVE": set(),
    "RESOLVED": set(),
}


@router.post("/incidents")
async def create_incident(
    incident: Incident,
    db: Session = Depends(get_db),
):
    db_incident = IncidentModel(
        incident_id=incident.incident_id,
        camera_id=incident.camera_id,
        city=incident.city,
        precinct=incident.precinct,
        location=incident.location,
        latitude=incident.latitude,
        longitude=incident.longitude,
        confidence=incident.confidence,
        violence_type=incident.violence_type,
        clip_path=incident.clip_path,
        thumbnail_path=incident.thumbnail_path,
        status=incident.status,
        priority_score=incident.priority_score,
        created_at=incident.timestamp,
    )

    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)

    await manager.broadcast(
        {
            "type": "NEW_INCIDENT",
            "incident_id": incident.incident_id,
            "camera_id": incident.camera_id,
            "location": incident.location,
            "confidence": incident.confidence,
            "status": incident.status,
        }
    )

    return {
        "message": "Incident stored successfully",
        "incident_id": incident.incident_id,
    }


@router.get("/incidents")
async def get_incidents(
    city: Optional[str] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(IncidentModel)

    scoped_city = city or current_user.get("city")

    if scoped_city:
        query = query.filter(IncidentModel.city == scoped_city)

    incidents = query.order_by(IncidentModel.id.desc()).all()

    return incidents


@router.get("/incidents/{incident_id}")
async def get_incident(
    incident_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    incident = (
        db.query(IncidentModel)
        .filter(IncidentModel.incident_id == incident_id)
        .first()
    )

    if not incident:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    if current_user.get("role") != "Admin" and incident.city != current_user.get("city"):
        raise HTTPException(
            status_code=403,
            detail="Permission denied",
        )

    return incident


@router.patch("/incidents/{incident_id}/status")
async def update_incident_status(
    incident_id: str,
    status: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if status == "ESCALATED":
        require_role(
            current_user,
            ["Supervisor", "Admin"],
        )

    incident = (
        db.query(IncidentModel)
        .filter(IncidentModel.incident_id == incident_id)
        .first()
    )

    if not incident:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    if current_user.get("role") != "Admin" and incident.city != current_user.get("city"):
        raise HTTPException(
            status_code=403,
            detail="Permission denied",
        )

    if status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="Invalid incident status",
        )

    if status != incident.status:
        allowed_next_statuses = ALLOWED_STATUS_TRANSITIONS.get(
            incident.status,
            set(),
        )

        if status not in allowed_next_statuses:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Cannot transition incident from "
                    f"{incident.status} to {status}"
                ),
            )

    incident.status = status

    db.commit()

    log_action(
        db=db,
        incident_id=incident_id,
        operator_id=current_user.get("sub", "UNKNOWN"),
        action=status,
        notes="Status changed from dashboard",
    )

    await manager.broadcast(
        {
            "type": "STATUS_UPDATED",
            "incident_id": incident_id,
            "status": status,
        }
    )

    return {
        "message": "Status updated",
        "incident_id": incident_id,
        "new_status": status,
    }
