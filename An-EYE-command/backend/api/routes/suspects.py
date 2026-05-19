from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.database.session import get_db
from backend.models.suspect_model import Suspect, SuspectIncident
from backend.schemas.suspect_schema import SuspectCreate, SuspectResponse
from backend.services.audit_logger import log_action
from backend.websocket.manager import manager

router = APIRouter()


@router.post("/suspects")
async def create_or_update_suspect(
    data: SuspectCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    suspect = db.query(Suspect).filter(Suspect.suspect_id == data.suspect_id).first()

    if suspect:
        suspect.violence_count = data.violence_count
        suspect.risk_level = data.risk_level
        if data.last_seen:
            suspect.last_seen = data.last_seen
        suspect.latest_camera = data.latest_camera
        suspect.latest_location = data.latest_location

        db.commit()

        log_action(
            db=db,
            incident_id=None,
            operator_id=current_user.get("sub", "SYSTEM"),
            action="SUSPECT_UPDATED",
            notes=f"Updated suspect {data.suspect_id}",
        )

        return {"message": "updated"}

    new_suspect = Suspect(
        suspect_id=data.suspect_id,
        face_image=data.face_image,
        violence_count=data.violence_count,
        risk_level=data.risk_level,
        embedding=data.embedding,
        first_seen=data.first_seen,
        last_seen=data.last_seen,
        latest_camera=data.latest_camera,
        latest_location=data.latest_location,
    )

    db.add(new_suspect)
    db.commit()

    log_action(
        db=db,
        incident_id=None,
        operator_id=current_user.get("sub", "SYSTEM"),
        action="SUSPECT_CREATED",
        notes=f"Created suspect {data.suspect_id}",
    )

    return {"message": "created"}


@router.get("/suspects", response_model=List[SuspectResponse])
async def get_suspects(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    suspects = db.query(Suspect).all()
    return suspects
