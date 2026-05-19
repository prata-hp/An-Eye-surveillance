from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String

from backend.database.base import Base


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    incident_id = Column(String)

    operator_id = Column(String)

    action = Column(String)

    notes = Column(String)

    timestamp = Column(DateTime, default=datetime.utcnow)
