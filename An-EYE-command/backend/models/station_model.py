from sqlalchemy import Column
from sqlalchemy import Float
from sqlalchemy import Integer
from sqlalchemy import String

from backend.database.base import Base


class PoliceStationModel(Base):
    __tablename__ = "police_stations"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String)

    latitude = Column(Float)
    longitude = Column(Float)

    city = Column(String)
