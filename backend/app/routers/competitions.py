from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import SessionLocal
from .. import models
from ..models import CompetitionCategory
from ..security import get_current_user, require_role
from sqlalchemy import func
router = APIRouter(prefix="/competitions", tags=["competitions"])
class CompetitionCreate(BaseModel):
    name: str
    category: CompetitionCategory


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/")
def list_competitions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    comps = db.query(models.Competition).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "category": c.category,
        }
        for c in comps
    ]


@router.post("/")
def create_competition(
    competition: CompetitionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role('ADMIN')),
):
    # Prevent duplicate competition names
    existing = db.query(models.Competition).filter(models.Competition.name == competition.name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Competition with this name already exists")
    db_competition = models.Competition(name=competition.name, category=competition.category)
    db.add(db_competition)
    db.commit()
    db.refresh(db_competition)
    # Audit log for competition creation
    audit = models.AuditLog(
        user_id=current_user.id,
        action='create_competition',
        entity_type='Competition',
        entity_id=db_competition.id,
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return {"id": db_competition.id, "name": db_competition.name}



@router.get("/{competition_id}")
def get_competition(competition_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    comp = db.get(models.Competition, competition_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    return {"id": comp.id, "name": comp.name, "category": comp.category, "teams_count": len(comp.teams), "deliverables_count": len(comp.deliverables)}


@router.put("/{competition_id}")
def update_competition(competition_id: int, name: str = None, category: str = None, db: Session = Depends(get_db), current_user: models.User = Depends(require_role("ADMIN"))):
    comp = db.get(models.Competition, competition_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    if name is not None:
        comp.name = name
    if category is not None:
        comp.category = CompetitionCategory(category)
    db.commit()
    db.refresh(comp)
    return {"id": comp.id, "name": comp.name, "category": comp.category}


@router.delete("/{competition_id}")
def delete_competition(competition_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(require_role("ADMIN"))):
    comp = db.get(models.Competition, competition_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    db.delete(comp)
    db.commit()
    return {"detail": "Competition deleted"}


@router.get("/{competition_id}/teams")
def list_competition_teams(competition_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    comp = db.get(models.Competition, competition_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    return [{"id": t.id, "name": t.name, "members_count": len(t.members)} for t in comp.teams]


@router.get("/{competition_id}/leaderboard")
def leaderboard(competition_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    comp = db.get(models.Competition, competition_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    results = db.query(models.Team.id, models.Team.name, func.coalesce(func.sum(models.EvaluationScore.score), 0).label("total"), func.count(models.EvaluationScore.id).label("num")).outerjoin(models.Evaluation, models.Evaluation.team_id == models.Team.id).outerjoin(models.EvaluationScore, models.EvaluationScore.evaluation_id == models.Evaluation.id).filter(models.Team.competition_id == competition_id).group_by(models.Team.id, models.Team.name).order_by(func.coalesce(func.sum(models.EvaluationScore.score), 0).desc()).all()
    return [{"rank": i+1, "team_id": r[0], "team_name": r[1], "total_score": float(r[2]), "num_scores": r[3]} for i, r in enumerate(results)]
