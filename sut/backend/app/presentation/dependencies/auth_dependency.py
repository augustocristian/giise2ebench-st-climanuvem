from typing import Annotated
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.business.auth_service import InvalidTokenError, authenticate_user

security = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)]
):
    if credentials is None:
        raise HTTPException(status_code=403, detail="Not authenticated")

    try:
        token = credentials.credentials
        return authenticate_user(token)
    except InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
