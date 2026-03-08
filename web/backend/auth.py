from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from config import ADMIN_API_KEY

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    # If no key is configured, auth is disabled (dev mode)
    if not ADMIN_API_KEY:
        return True
    if api_key != ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key. Set X-API-Key header.",
        )
    return True
