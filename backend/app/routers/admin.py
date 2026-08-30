from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from .. import models
from ..security import get_current_user, get_password_hash, require_role

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(current_user: models.User = Depends(get_current_user)):
    if current_user.role.value != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return current_user


@router.get("/users")
def list_users(db: Session = Depends(get_db), admin: models.User = Depends(require_role('ADMIN'))):
    return db.query(models.User).all()


@router.post("/users")
def create_user(
    email: str,
    password: str,
    role: str = "TEAM_MEMBER",
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_role('ADMIN')),
):
    if role not in models.UserRole.__members__:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
    if db.query(models.User).filter(models.User.email == email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user = models.User(
        email=email,
        password_hash=get_password_hash(password),
        role=models.UserRole[role],
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    # Audit log for user creation
    audit = models.AuditLog(
        user_id=admin.id,
        action='create_user',
        entity_type='User',
        entity_id=user.id,
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return {"id": user.id, "email": user.email, "role": user.role.value}


@router.get("/evaluation-criteria")
def list_criteria(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return db.query(models.EvaluationCriteria).all()


@router.post("/evaluation-criteria")
def create_criterion(
    name: str,
    weight: float,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_role('ADMIN')),
):
    if weight <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Weight must be a positive number",
        )
    current_total = db.query(
        func.coalesce(func.sum(models.EvaluationCriteria.weight), 0)
    ).scalar()
    if current_total + weight > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Criterion weights must total exactly 100% (current total: {current_total})",
        )
    criterion = models.EvaluationCriteria(name=name, weight=weight)
    db.add(criterion)
    db.commit()
    db.refresh(criterion)
    return {"id": criterion.id, "name": criterion.name, "weight": criterion.weight}


@router.get("/audit-logs")
def list_audit_logs(
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_role('ADMIN')),
):
    return db.query(models.AuditLog).all()
