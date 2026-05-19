from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class SuspectCreate(BaseModel):
    suspect_id: str
    face_image: str
    violence_count: int = 1
    risk_level: str = "LOW"
    embedding: List[float] | None = None
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    latest_camera: Optional[str] = None
    latest_location: Optional[str] = None


class SuspectResponse(BaseModel):
    suspect_id: str
    face_image: str | None = None
    violence_count: int
    risk_level: str
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    latest_camera: Optional[str] = None
    latest_location: Optional[str] = None

    class Config:
        from_attributes = True
