import pathlib

TEAMS = pathlib.Path(r"D:\AIYouthInnovation2026\backend\app\routers\teams.py")
content = TEAMS.read_text()

content += '''


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
        raise HTTPException(status_code=404, detail="Member not found")
    db.delete(member)
    db.commit()
    return {"detail": "Member removed"}
'''

TEAMS.write_text(content)
print("Done! teams.py updated")