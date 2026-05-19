from datetime import datetime
from typing import Optional
from backend.services.camera_service import get_camera
from pydantic import BaseModel


class Incident(BaseModel):
    incident_id: str

    camera_id: str
    city: str
    precinct: str
    location: str

    latitude: float
    longitude: float

    timestamp: datetime

    confidence: float
    violence_type: str

    clip_path: str
    thumbnail_path: Optional[str] = None

    status: str

    priority_score: float = 0.0
