from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models
from ..security import (
    verify_password,
    create_access_token,
    get_current_user,
    get_password_hash,
    require_role,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    token = create_access_token(str(user.id), user.role.value)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
def read_me(current_user: models.User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role.value,
    }


@router.post("/register")
def register(
    email: str,
    password: str,
    db: Session = Depends(get_db),
):
    # Self-registration is restricted to TEAM_MEMBER accounts only.
    # Admin/Judge accounts must be created via the admin endpoints to
    # prevent privilege escalation.
    existing = db.query(models.User).filter(models.User.email == email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user = models.User(
        email=email,
        password_hash=get_password_hash(password),
        role=models.UserRole.TEAM_MEMBER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email, "role": user.role.value}


@router.post("/change-password")
def change_password(
    current_password: str = Body(...),
    new_password: str = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not verify_password(current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    if len(new_password) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password must be at least 6 characters")
    user = db.get(models.User, current_user.id)
    user.password_hash = get_password_hash(new_password)
    db.commit()
    db.refresh(user)
    return {"success": True, "message": "Password changed"}


@router.post("/reset-password")
def reset_password(
    user_id: int = Body(...),
    new_password: str = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("ADMIN")),
):
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not new_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password cannot be empty")
    user.password_hash = get_password_hash(new_password)
    db.commit()
    db.refresh(user)
    return {"success": True, "user_id": user.id, "email": user.email}