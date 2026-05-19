from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from pydantic import BaseModel
import requests
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.database.session import get_db
from backend.models.incident_model import IncidentModel
from backend.services.audit_logger import log_action
from backend.services.police_locator import get_nearby_police_stations
from backend.websocket.manager import manager
from datetime import datetime

from backend.services.twilio_service import (
    send_sms,
    make_call,
)


router = APIRouter(tags=["dispatch"])


class DispatchReport(BaseModel):
    incident_id: str
    station: str
    note: str = ""


@router.get("/nearby-stations")
def nearby_stations(
    lat: float,
    lng: float,
    radius: int = 5000,
):
    try:
        return get_nearby_police_stations(
            lat,
            lng,
            radius,
        )
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502,
            detail="Police station lookup failed",
        ) from exc


@router.get("/dispatch/{incident_id}")
async def get_dispatch_info(
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

    try:
        nearest_stations = get_nearby_police_stations(
            incident.latitude,
            incident.longitude,
        )
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502,
            detail="Police station lookup failed",
        ) from exc

    return {
        "incident_id": incident_id,
        "nearest_stations": nearest_stations,
        "source": "OpenStreetMap",
    }


@router.post("/dispatch-report")
async def send_dispatch_report(
    report: DispatchReport,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    incident = (
        db.query(IncidentModel)
        .filter(IncidentModel.incident_id == report.incident_id)
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

    if incident.status not in {
        "NEW",
        "UNDER_REVIEW",
        "PENDING",
        "ESCALATED",
    }:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot dispatch incident from {incident.status}",
        )

    incident.status = "ESCALATED"
    db.commit()

    google_maps_url = (
        f"https://maps.google.com/?q="
        f"{incident.latitude},{incident.longitude}"
    )

    dispatch_time = datetime.now().strftime(
        "%d %b %Y, %I:%M %p"
    )

    message = f"""
AN-EYE VIOLENCE ALERT

Incident ID:
{incident.incident_id}

Location:
{incident.location}

Camera:
{incident.camera_id}

Confidence:
{round((incident.confidence or 0) * 100)}%

Escalation Time:
{dispatch_time}

Google Maps:
{google_maps_url}

STATUS:
ESCALATED
"""

    print("Sending SMS...")
    send_sms(message)

    print("Triggering emergency call...")
    make_call(
        f"""
        Emergency alert from A N Eye.
        Violence detected at {incident.location}.
        Immediate response recommended.
        """
    )

    note = (
        f"Dispatch report sent to {report.station}."
        f" Officer note: {report.note or 'None'}"
    )

    log_action(
        db=db,
        incident_id=report.incident_id,
        operator_id=current_user.get("sub", "UNKNOWN"),
        action="DISPATCH_REPORT_SENT",
        notes=note,
    )

    await manager.broadcast(
        {
            "type": "STATUS_UPDATED",
            "incident_id": report.incident_id,
            "status": "ESCALATED",
        }
    )

    return {
        "message": "Dispatch report sent",
        "incident_id": report.incident_id,
        "station": report.station,
        "new_status": "ESCALATED",
    }
