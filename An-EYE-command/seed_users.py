from sqlalchemy.orm import sessionmaker

from backend.auth.security import hash_password
from backend.database.connection import engine
from backend.models.user_model import UserModel


Session = sessionmaker(bind=engine)

db = Session()

users = [
    {
        "username": "operator1",
        "password": "password123",
        "role": "Operator",
        "precinct": "South Belt",
        "city": "Patna",
    },
    {
        "username": "supervisor1",
        "password": "password123",
        "role": "Supervisor",
        "precinct": "South Belt",
        "city": "Patna",
    },
    {
        "username": "admin1",
        "password": "password123",
        "role": "Admin",
        "precinct": "Central Command",
        "city": "Patna",
    },
]

for user in users:
    existing_user = (
        db.query(UserModel)
        .filter(UserModel.username == user["username"])
        .first()
    )

    values = {
        "username": user["username"],
        "password_hash": hash_password(user["password"]),
        "role": user["role"],
        "precinct": user["precinct"],
        "city": user["city"],
    }

    if existing_user:
        for key, value in values.items():
            setattr(existing_user, key, value)
    else:
        db.add(UserModel(**values))

db.commit()
db.close()

print("Users seeded successfully")
