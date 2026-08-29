import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError
from app.database import SessionLocal
from app.auth_utils import decode_access_token
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        user_id = uuid.UUID(user_id)
    except (JWTError, ValueError, TypeError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user
