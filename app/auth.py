from fastapi import HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from .config import get_settings

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    settings = get_settings()
    if credentials.credentials != settings.auth_token:
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials
