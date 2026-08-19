import pathlib

COMP = pathlib.Path(r"D:\AIYouthInnovation2026\backend\app\routers\competitions.py")
content = COMP.read_text()

# Add imports
content = content.replace(
    "from ..security import get_current_user, require_role",
    "from ..security import get_current_user, require_role\nfrom sqlalchemy import func"
)

# New endpoints
content += '''


@router.get("/{competition_id}")
def get_competition(competition_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    comp = db.get(models.Competition, competition_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    return {"id": comp.id, "name": comp.name, "category": comp.category.value if comp.category else None, "teams_count": len(comp.teams), "deliverables_count": len(comp.deliverables)}


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
    return {"id": comp.id, "name": comp.name, "category": comp.category.value if comp.category else None}


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
'''

COMP.write_text(content)
print("Done! competitions.py updated")