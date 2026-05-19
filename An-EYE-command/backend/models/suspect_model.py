from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Integer
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import JSON

from backend.database.base import Base

from datetime import datetime


class Suspect(Base):

    __tablename__ = "suspects"

    suspect_id = Column(
        String,
        primary_key=True,
        index=True
    )

    face_image = Column(String)

    violence_count = Column(
        Integer,
        default=1
    )

    risk_level = Column(
        String,
        default="LOW"
    )

    embedding = Column(JSON)

    first_seen = Column(
        DateTime,
        default=datetime.utcnow
    )

    last_seen = Column(
        DateTime,
        default=datetime.utcnow
    )

    latest_camera = Column(String)

    latest_location = Column(String)


class SuspectIncident(Base):

    __tablename__ = "suspect_incidents"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    suspect_id = Column(
        String,
        ForeignKey("suspects.suspect_id")
    )

    incident_id = Column(String)

    timestamp = Column(
        DateTime,
        default=datetime.utcnow
    )

    camera_id = Column(String)

    location = Column(String)

    clip_url = Column(String)
