from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String

from backend.database.base import Base


class OperatorModel(Base):
    __tablename__ = "operators"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String)

    shift = Column(String)

    precinct = Column(String)

    city = Column(String)

    role = Column(String)
