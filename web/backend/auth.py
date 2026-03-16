from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from jwt_auth import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def verify_api_key(token: str = Depends(oauth2_scheme)) -> str:
    username = decode_token(token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return username
