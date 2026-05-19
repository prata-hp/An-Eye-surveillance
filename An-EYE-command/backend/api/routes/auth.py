from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.auth.security import create_access_token
from backend.auth.security import verify_password
from backend.database.session import get_db
from backend.models.user_model import UserModel
from backend.schemas.login import LoginRequest


router = APIRouter()


@router.post("/login")
async def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(UserModel)
        .filter(UserModel.username == credentials.username)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
        )

    if not verify_password(
        credentials.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
        )

    token = create_access_token(
        {
            "sub": user.username,
            "role": user.role,
            "city": user.city,
            "precinct": user.precinct,
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "city": user.city,
        "precinct": user.precinct,
    }
