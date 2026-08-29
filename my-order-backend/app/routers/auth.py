from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserOut, Token, LoginRequest
from app.auth_utils import hash_password, verify_password, create_access_token
from app.models.user import UserRole
from app.security import limit_auth_attempts

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db), _: None = Depends(limit_auth_attempts)):
    existing = db.query(User).filter(User.phone == payload.phone).first()
    if existing:
        raise HTTPException(status_code=400, detail="Phone number already registered")

    user = User(
        name=payload.name,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role=UserRole(payload.role.value),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db), _: None = Depends(limit_auth_attempts)):
    user = db.query(User).filter(User.phone == payload.phone).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid phone or password")

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return Token(access_token=token)
