from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import Integer
from sqlalchemy import String

from backend.database.base import Base


class IncidentModel(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)

    incident_id = Column(String, unique=True)

    camera_id = Column(String)

    city = Column(String)
    precinct = Column(String)
    location = Column(String)

    latitude = Column(Float)
    longitude = Column(Float)

    confidence = Column(Float)

    violence_type = Column(String)

    clip_path = Column(String)
    thumbnail_path = Column(String)

    status = Column(String)

    priority_score = Column(Float)

    created_at = Column(DateTime)
