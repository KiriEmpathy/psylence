from datetime import datetime, timezone
from fastapi import Depends, HTTPException, Request, status
from jose import jwt, JWTError
from app.config import settings
from app.users.dao import UserDAO


def get_token(request: Request):
    token = request.cookies.get("user_access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Access token not found in cookies")
    return token

def get_refresh_token(request: Request):
    token = request.cookies.get("user_refresh_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Refresh token not found"
        )
    return token

async def get_current_user(token: str = Depends(get_token)):
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, settings.algorithm
        )
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unable to decode token")
    expire: str = payload.get("exp")
    if not expire or int(expire) < datetime.now(timezone.utc).timestamp():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session has expired")
    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Id not found in payload")
    user = await UserDAO.find_by_id(int(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="The user was not found in the database")
    
    return user

async def get_current_user_by_refresh(request: Request, token: str = Depends(get_refresh_token)):
    try:
        payload = jwt.decode(token, settings.JWT_REFRESH_SECRET_KEY, settings.algorithm)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    
    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User ID not found in token")
    
    db_session = await UserDAO.find_one_or_none(id=user_id)
    
    if not db_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Active session not found")
    
    if db_session.expires_at < datetime.now(timezone.utc):
        await UserDAO.reset_session(user_id)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")
    
    current_ip = request.client.host

    if str(db_session.last_ip) != current_ip:
        await UserDAO.reset_session(user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Security breach: IP address mismatch. Please log in again."
        )
    
    user = await UserDAO.find_by_id(int(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
    
    