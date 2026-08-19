from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import SessionLocal
from .. import models
from ..security import get_current_user, require_role

router = APIRouter(prefix="/judges", tags=["judges"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _get_or_404(db, model, pk):
    obj = db.get(model, pk)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{model.__name__} not found")
    return obj


@router.post("")
def create_judge(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role('ADMIN')),
):
    _get_or_404(db, models.User, user_id)
    judge = models.Judge(user_id=user_id)
    db.add(judge)
    db.commit()
    db.refresh(judge)
    # Audit log for judge creation
    audit = models.AuditLog(
        user_id=current_user.id,
        action='create_judge',
        entity_type='Judge',
        entity_id=judge.id,
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return {"id": judge.id, "user_id": judge.user_id}


@router.post("/assignments")
def create_assignment(
    judge_id: int,
    team_id: int,
    competition_id: int,
    assigned_by: int = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role('ADMIN')),
):
    _get_or_404(db, models.Judge, judge_id)
    _get_or_404(db, models.Team, team_id)
    _get_or_404(db, models.Competition, competition_id)
    assignment = models.JudgeAssignment(
        judge_id=judge_id,
        team_id=team_id,
        competition_id=competition_id,
        assigned_by=assigned_by,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return {"id": assignment.id}


@router.get("/my-assignments")
def list_my_assignments(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role('JUDGE')),
):
    judge = db.query(models.Judge).filter(models.Judge.user_id == current_user.id).first()
    if not judge:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not a judge")
    assignments = db.query(models.JudgeAssignment).filter(models.JudgeAssignment.judge_id == judge.id).all()
    result = []
    for a in assignments:
        team = db.get(models.Team, a.team_id)
        comp = db.get(models.Competition, a.competition_id)
        result.append({
            "id": a.id,
            "judge_id": a.judge_id,
            "team_id": a.team_id,
            "team_name": team.name if team else None,
            "competition_id": a.competition_id,
            "competition_name": comp.name if comp else None,
            "assigned_at": a.assigned_at,
        })
    return result


@router.get("/evaluations/criteria")
def get_criteria(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role('JUDGE')),
):
    return db.query(models.EvaluationCriteria).all()


@router.post("/evaluations/mine")
def create_my_evaluation(
    team_id: int,
    competition_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role('JUDGE')),
):
    judge = db.query(models.Judge).filter(models.Judge.user_id == current_user.id).first()
    if not judge:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not a judge")
    assignment = db.query(models.JudgeAssignment).filter(
        models.JudgeAssignment.judge_id == judge.id,
        models.JudgeAssignment.team_id == team_id,
        models.JudgeAssignment.competition_id == competition_id,
    ).first()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Judge not assigned to this team/competition")
    existing = db.query(models.Evaluation).filter(
        models.Evaluation.judge_id == judge.id,
        models.Evaluation.team_id == team_id,
        models.Evaluation.competition_id == competition_id,
    ).first()
    if existing:
        return {"id": existing.id, "existing": True}
    evaluation = models.Evaluation(
        judge_id=judge.id,
        team_id=team_id,
        competition_id=competition_id,
    )
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    return {"id": evaluation.id, "existing": False}


@router.get("/competitions/{competition_id}/evaluations")
def list_evaluations(
    competition_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role('ADMIN')),
):
    return db.query(models.Evaluation).filter(
        models.Evaluation.competition_id == competition_id
    ).all()


@router.post("/evaluations")
def create_evaluation(
    judge_id: int,
    team_id: int,
    competition_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role('ADMIN')),
):
    _get_or_404(db, models.Judge, judge_id)
    _get_or_404(db, models.Team, team_id)
    _get_or_404(db, models.Competition, competition_id)
    evaluation = models.Evaluation(
        judge_id=judge_id,
        team_id=team_id,
        competition_id=competition_id,
    )
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    # Audit log for evaluation creation
    audit = models.AuditLog(
        user_id=current_user.id,
        action='create_evaluation',
        entity_type='Evaluation',
        entity_id=evaluation.id,
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return {"id": evaluation.id}


@router.post("/evaluations/{evaluation_id}/scores")
def add_score(
    evaluation_id: int,
    criterion_id: int,
    score: float,
    comment: str = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role('JUDGE')),
):
    evaluation = db.get(models.Evaluation, evaluation_id)
    if evaluation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found")
    judge = db.query(models.Judge).filter(models.Judge.user_id == current_user.id).first()
    if not judge or evaluation.judge_id != judge.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Judge not assigned to this evaluation")
    if db.get(models.EvaluationCriteria, criterion_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Criterion not found")
    existing = db.query(models.EvaluationScore).filter(
        models.EvaluationScore.evaluation_id == evaluation_id,
        models.EvaluationScore.criterion_id == criterion_id,
    ).first()
    if existing:
        existing.score = score
        existing.comment = comment
        db.add(existing)
    else:
        score_row = models.EvaluationScore(
            evaluation_id=evaluation_id,
            criterion_id=criterion_id,
            score=score,
            comment=comment,
        )
        db.add(score_row)
        score_row = score_row
    db.commit()
    db.refresh(existing if existing else score_row)
    result = existing if existing else score_row
    audit = models.AuditLog(
        user_id=current_user.id,
        action='add_score',
        entity_type='EvaluationScore',
        entity_id=result.id,
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return {"id": result.id, "score": result.score, "comment": result.comment}


@router.get("/evaluations")
def list_my_evaluations(
    comp_id: int = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role('JUDGE')),
):
    judge = db.query(models.Judge).filter(models.Judge.user_id == current_user.id).first()
    if not judge:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not a judge")
    query = db.query(models.Evaluation).join(models.EvaluationScore, isouter=True).filter(
        models.Evaluation.judge_id == judge.id,
    )
    if comp_id is not None:
        query = query.filter(models.Evaluation.competition_id == comp_id)
    evals = query.all()
    return [
        {
            "id": e.id,
            "team_id": e.team_id,
            "competition_id": e.competition_id,
            "created_at": e.created_at,
            "scores": [
                {
                    "criterion": s.criterion.name,
                    "score": s.score,
                    "comment": s.comment,
                }
                for s in e.scores
            ],
        }
        for e in evals
    ]


@router.get("/competitions/{competition_id}/scores")
def get_competition_scores(
    competition_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role('JUDGE')),
):
    """Dashboard: all teams with their scores for a competition."""
    judge = db.query(models.Judge).filter(models.Judge.user_id == current_user.id).first()
    if not judge:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not a judge")
    assigned_team_ids = [
        ja.team_id
        for ja in db.query(models.JudgeAssignment).filter(
            models.JudgeAssignment.judge_id == judge.id,
            models.JudgeAssignment.competition_id == competition_id,
        ).all()
    ]
    if not assigned_team_ids:
        return []
    evaluations = db.query(models.Evaluation).filter(
        models.Evaluation.competition_id == competition_id,
        models.Evaluation.team_id.in_(assigned_team_ids),
    ).all()
    scores = db.query(models.EvaluationScore).join(models.Evaluation).filter(
        models.Evaluation.competition_id == competition_id,
        models.Evaluation.team_id.in_(assigned_team_ids),
    ).all()
    criteria = db.query(models.EvaluationCriteria).all()
    num_judges = len(set(e.judge_id for e in evaluations))
    result = []
    for team_id in assigned_team_ids:
        team = db.get(models.Team, team_id)
        crit_vals = {}
        for s in scores:
            if s.evaluation.team_id == team_id:
                crit_vals.setdefault(s.criterion.name, []).append(s.score)
        team_scores = {}
        total = 0.0
        for crit_name, vals in crit_vals.items():
            avg = sum(vals) / len(vals)
            team_scores[crit_name] = {"score": round(avg, 1)}
            total += avg
        result.append({
            "team_id": team_id,
            "team_name": team.name if team else None,
            "total_score": round(total, 1),
            "criteria_scores": team_scores,
            "num_judges": num_judges,
            "max_possible": sum(c.weight for c in criteria),
        })
    return result


@router.get("/submissions")
def get_judge_all_submissions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role('JUDGE')),
):
    """List all submissions (with files) across all competitions for a judge's assigned teams."""
    judge = db.query(models.Judge).filter(models.Judge.user_id == current_user.id).first()
    if not judge:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not a judge")
    assignments = db.query(models.JudgeAssignment).filter(
        models.JudgeAssignment.judge_id == judge.id,
    ).all()
    assigned_team_ids = [a.team_id for a in assignments]
    if not assigned_team_ids:
        return []
    submissions = db.query(models.Submission).join(models.Deliverable).filter(
        models.Submission.team_id.in_(assigned_team_ids),
    ).all()
    result = []
    for sub in submissions:
        team = db.get(models.Team, sub.team_id)
        deliverable = db.get(models.Deliverable, sub.deliverable_id)
        competition = db.get(models.Competition, deliverable.competition_id) if deliverable else None
        files = db.query(models.SubmissionFile).filter(
            models.SubmissionFile.submission_id == sub.id
        ).all()
        result.append({
            "submission_id": sub.id,
            "team_id": sub.team_id,
            "team_name": team.name if team else None,
            "deliverable_id": sub.deliverable_id,
            "deliverable_name": deliverable.name if deliverable else None,
            "deliverable_category": deliverable.category if deliverable else None,
            "competition_id": deliverable.competition_id if deliverable else None,
            "competition_name": competition.name if competition else None,
            "status": sub.status.value,
            "version": sub.version,
            "updated_at": sub.updated_at,
            "files": [
                {
                    "id": f.id,
                    "original_filename": f.original_filename,
                    "file_type": f.file_type,
                    "file_size": f.file_size,
                    "uploaded_at": f.uploaded_at,
                    "submitted_at": f.submitted_at,
                    "version": f.version,
                }
                for f in files
            ],
        })
    return result
