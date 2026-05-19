from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String

from backend.database.base import Base


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String, unique=True)

    password_hash = Column(String)

    role = Column(String)

    precinct = Column(String)

    city = Column(String)
