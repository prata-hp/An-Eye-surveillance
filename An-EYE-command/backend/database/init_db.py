from backend.database.base import Base
from backend.database.connection import engine
from backend.models.audit_log_model import AuditLogModel
from backend.models.incident_model import IncidentModel
from backend.models.operator_model import OperatorModel
from backend.models.station_model import PoliceStationModel
from backend.models.user_model import UserModel
from backend.models.suspect_model import Suspect, SuspectIncident


def initialize_database():
    Base.metadata.create_all(bind=engine)

    print("Database tables created successfully")
