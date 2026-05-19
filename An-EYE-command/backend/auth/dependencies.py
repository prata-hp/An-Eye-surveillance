from fastapi import Depends
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from jose import JWTError
from jose import jwt

from backend.auth.security import ALGORITHM
from backend.auth.security import SECRET_KEY


security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        return payload

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )
