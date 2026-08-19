from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import SessionLocal
from .. import models
from ..security import get_current_user, require_role

class TeamCreate(BaseModel):
    name: str
    competition_id: int

router = APIRouter(prefix="/teams", tags=["teams"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("")
def list_teams(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return db.query(models.Team).all()


@router.post("")
def create_team(
    team: TeamCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role('ADMIN')),
):
    if db.get(models.Competition, team.competition_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competition not found")
    existing = db.query(models.Team).filter(models.Team.competition_id == team.competition_id, models.Team.name == team.name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Team with this name already exists in the competition")
    new_team = models.Team(name=team.name, competition_id=team.competition_id)
    db.add(new_team)
    db.commit()
    db.refresh(new_team)
    return {"id": new_team.id, "name": new_team.name, "competition_id": new_team.competition_id}


@router.get("/mine")
def get_my_team(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    member = db.query(models.TeamMember).filter(models.TeamMember.user_id == current_user.id).first()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You are not a member of any team")
    team = db.get(models.Team, member.team_id)
    return {
        "id": team.id,
        "name": team.name,
        "competition_id": team.competition_id,
        "members": [{"id": m.id, "user_id": m.user_id, "email": m.user.email, "is_leader": m.is_leader} for m in team.members],
    }


@router.get("/mine/submissions")
def get_my_team_submissions(
    competition_id: int = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    member = db.query(models.TeamMember).filter(models.TeamMember.user_id == current_user.id).first()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You are not a member of any team")
    query = db.query(models.Submission).filter(models.Submission.team_id == member.team_id)
    if competition_id is not None:
        query = query.join(models.Deliverable).filter(models.Deliverable.competition_id == competition_id)
    return query.all()


@router.post("/{team_id}/members")
def add_member(
    team_id: int,
    user_id: int,
    is_leader: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role('ADMIN')),
):
    if db.get(models.Team, team_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    if db.get(models.User, user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    member = models.TeamMember(team_id=team_id, user_id=user_id, is_leader=is_leader)
    db.add(member)
    db.commit()
    db.refresh(member)
    return {"id": member.id, "team_id": member.team_id, "user_id": member.user_id}


@router.get("/{team_id}")
def get_team(team_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    team = db.get(models.Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return {
        "id": team.id,
        "name": team.name,
        "competition_id": team.competition_id,
        "members": [{"id": m.id, "user_id": m.user_id, "email": m.user.email, "is_leader": m.is_leader} for m in team.members],
    }


@router.get("/{team_id}/members")
def list_members(team_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    team = db.get(models.Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return [{"id": m.id, "user_id": m.user_id, "email": m.user.email, "is_leader": m.is_leader} for m in team.members]


@router.delete("/{team_id}")
def delete_team(team_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(require_role("ADMIN"))):
    team = db.get(models.Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    db.delete(team)
    db.commit()
    return {"detail": "Team deleted"}


@router.delete("/{team_id}/members/{user_id}")
def remove_member(team_id: int, user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(require_role("ADMIN"))):
    member = db.query(models.TeamMember).filter(models.TeamMember.team_id == team_id, models.TeamMember.user_id == user_id).first()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    db.delete(member)
    db.commit()
    return {"detail": "Member removed"}
