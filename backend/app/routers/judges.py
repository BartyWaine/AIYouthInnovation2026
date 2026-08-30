from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timezone

from ..database import get_db
from .. import models
from ..security import get_current_user, require_role

router = APIRouter(prefix="/judges", tags=["judges"])

VALID_TRANSITIONS = {
    models.EvaluationStatus.OPEN: {models.EvaluationStatus.SUBMITTED, models.EvaluationStatus.LOCKED},
    models.EvaluationStatus.SUBMITTED: {models.EvaluationStatus.OPEN, models.EvaluationStatus.LOCKED},
    models.EvaluationStatus.LOCKED: {models.EvaluationStatus.FINALIZED, models.EvaluationStatus.OPEN},
    models.EvaluationStatus.FINALIZED: {models.EvaluationStatus.OPEN},  # only HEAD_JUDGE or ADMIN can reopen
}


def _get_or_404(db, model, pk):
    obj = db.get(model, pk)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{model.__name__} not found")
    return obj


def _audit_log(db, user, action, entity_type, entity_id, target_judge_id=None,
                old_value=None, new_value=None, reason=None, metadata=None):
    """Create an audit log entry. Must be called within the caller's transaction."""
    log = models.AuditLog(
        user_id=user.id,
        actor_role=user.role.value,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        target_judge_id=target_judge_id,
        old_value=str(old_value) if old_value is not None else None,
        new_value=str(new_value) if new_value is not None else None,
        reason=reason,
        metadata_json=metadata,
    )
    db.add(log)
    return log


def _require_head_judge_or_admin(current_user: models.User = Depends(get_current_user)):
    if current_user.role.value not in ("HEAD_JUDGE", "ADMIN"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Head Judge or Admin only")
    return current_user


def _require_judge_or_head(current_user: models.User = Depends(get_current_user)):
    if current_user.role.value not in ("JUDGE", "HEAD_JUDGE"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Judge or Head Judge only")
    return current_user


@router.post("")
def create_judge(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role('ADMIN')),
):
    user = _get_or_404(db, models.User, user_id)
    if user.role not in (models.UserRole.JUDGE, models.UserRole.HEAD_JUDGE):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must have JUDGE or HEAD_JUDGE role to create a judge record",
        )
    judge = models.Judge(user_id=user_id)
    db.add(judge)
    db.commit()
    db.refresh(judge)
    _audit_log(db, current_user, 'create_judge', 'Judge', judge.id)
    db.commit()
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
    current_user: models.User = Depends(_require_judge_or_head),
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
    current_user: models.User = Depends(_require_judge_or_head),
):
    return db.query(models.EvaluationCriteria).all()


@router.post("/evaluations/mine")
def create_my_evaluation(
    team_id: int,
    competition_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(_require_judge_or_head),
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
        return {"id": existing.id, "status": existing.status, "existing": True}
    evaluation = models.Evaluation(
        judge_id=judge.id,
        team_id=team_id,
        competition_id=competition_id,
        status=models.EvaluationStatus.OPEN,
    )
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    _audit_log(db, current_user, 'create_evaluation', 'Evaluation', evaluation.id)
    db.commit()
    return {"id": evaluation.id, "status": evaluation.status, "existing": False}


@router.get("/competitions/{competition_id}/evaluations")
def list_evaluations(
    competition_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(_require_head_judge_or_admin),
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
        status=models.EvaluationStatus.OPEN,
    )
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    _audit_log(db, current_user, 'create_evaluation', 'Evaluation', evaluation.id)
    db.commit()
    return {"id": evaluation.id}


# ─── Score helpers ────────────────────────────────────────────────────────────

def _validate_score(score: float, criterion: models.EvaluationCriteria) -> int:
    """Validate score is integer 1-10. Returns int score."""
    if score != int(score) or not (1 <= int(score) <= 10):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Score must be a whole number between 1 and 10",
        )
    return int(score)


def _check_evaluation_editable(evaluation: models.Evaluation, is_head_correction: bool = False):
    """Raise 403 if evaluation cannot be edited. HEAD_JUDGE corrections always allowed."""
    if is_head_correction:
        return
    if evaluation.status == models.EvaluationStatus.FINALIZED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Evaluation is finalized and cannot be edited"
        )
    if evaluation.status == models.EvaluationStatus.LOCKED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Evaluation is locked; only Head Judge can make corrections"
        )


# ─── Add / update score (ordinary judge) ─────────────────────────────────────

@router.post("/evaluations/{evaluation_id}/scores")
def add_score(
    evaluation_id: int,
    criterion_id: int,
    score: float,
    comment: str = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(_require_judge_or_head),
):
    evaluation = _get_or_404(db, models.Evaluation, evaluation_id)
    judge = db.query(models.Judge).filter(models.Judge.user_id == current_user.id).first()
    if not judge or evaluation.judge_id != judge.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to score this evaluation")

    _check_evaluation_editable(evaluation)

    criterion = _get_or_404(db, models.EvaluationCriteria, criterion_id)
    score_int = _validate_score(score, criterion)

    existing = db.query(models.EvaluationScore).filter(
        models.EvaluationScore.evaluation_id == evaluation_id,
        models.EvaluationScore.criterion_id == criterion_id,
    ).first()

    old_val = existing.score if existing else None
    if existing:
        existing.score = score_int
        existing.comment = comment
    else:
        existing = models.EvaluationScore(
            evaluation_id=evaluation_id,
            criterion_id=criterion_id,
            score=score_int,
            comment=comment,
        )
        db.add(existing)
    db.flush()

    try:
        _audit_log(
            db, current_user, 'add_score', 'EvaluationScore', existing.id,
            target_judge_id=evaluation.judge_id,
            old_value=old_val, new_value=score_int,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"id": existing.id, "score": existing.score, "comment": existing.comment}


# ─── HEAD_JUDGE: view all judges' scores ─────────────────────────────────────

@router.get("/all-scores")
def get_all_judges_scores(
    competition_id: int = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(_require_head_judge_or_admin),
):
    """HEAD_JUDGE or ADMIN: view all evaluations with per-judge scores."""
    query = db.query(models.Evaluation)
    if competition_id is not None:
        query = query.filter(models.Evaluation.competition_id == competition_id)
    evals = query.all()

    result = []
    for ev in evals:
        judge_row = db.get(models.Judge, ev.judge_id)
        judge_user = db.get(models.User, judge_row.user_id) if judge_row else None
        team = db.get(models.Team, ev.team_id)
        comp = db.get(models.Competition, ev.competition_id)
        result.append({
            "evaluation_id": ev.id,
            "judge_id": ev.judge_id,
            "judge_email": judge_user.email if judge_user else None,
            "team_id": ev.team_id,
            "team_name": team.name if team else None,
            "competition_id": ev.competition_id,
            "competition_name": comp.name if comp else None,
            "status": ev.status,
            "scores": [
                {
                    "score_id": s.id,
                    "criterion_id": s.criterion_id,
                    "criterion_name": s.criterion.name if s.criterion else None,
                    "score": s.score,
                    "comment": s.comment,
                    "corrected_by_user_id": s.corrected_by_user_id,
                    "corrected_at": s.corrected_at,
                }
                for s in ev.scores
            ],
            "created_at": ev.created_at,
            "updated_at": ev.updated_at,
        })
    return result


# ─── HEAD_JUDGE: correct another judge's mark ─────────────────────────────────

@router.patch("/evaluations/{evaluation_id}/scores/correct")
def correct_score(
    evaluation_id: int,
    criterion_id: int,
    score: float,
    reason: str = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(_require_head_judge_or_admin),
):
    if not reason or not reason.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Correction reason is required",
        )

    evaluation = _get_or_404(db, models.Evaluation, evaluation_id)
    if evaluation.status == models.EvaluationStatus.FINALIZED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Evaluation is finalized. Reopen it before correcting.",
        )

    criterion = _get_or_404(db, models.EvaluationCriteria, criterion_id)
    score_int = _validate_score(score, criterion)

    score_row = db.query(models.EvaluationScore).filter(
        models.EvaluationScore.evaluation_id == evaluation_id,
        models.EvaluationScore.criterion_id == criterion_id,
    ).first()

    old_val = score_row.score if score_row else None
    now = datetime.utcnow()

    if score_row:
        score_row.score = score_int
        score_row.comment = f"[Corrected by {current_user.email}] {reason.strip()}"
        score_row.corrected_by_user_id = current_user.id
        score_row.corrected_at = now
    else:
        score_row = models.EvaluationScore(
            evaluation_id=evaluation_id,
            criterion_id=criterion_id,
            score=score_int,
            comment=f"[Corrected by {current_user.email}] {reason.strip()}",
            corrected_by_user_id=current_user.id,
            corrected_at=now,
        )
        db.add(score_row)
    db.flush()

    try:
        _audit_log(
            db, current_user, 'correct_score', 'EvaluationScore', score_row.id,
            target_judge_id=evaluation.judge_id,
            old_value=old_val, new_value=score_int,
            reason=reason.strip(),
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "id": score_row.id,
        "old_value": old_val,
        "new_value": score_row.score,
        "corrected_by": current_user.email,
        "corrected_at": score_row.corrected_at,
        "reason": reason.strip(),
    }


# ─── Evaluation status: lock / finalize / reopen ──────────────────────────────

@router.post("/evaluations/{evaluation_id}/status")
def update_evaluation_status(
    evaluation_id: int,
    new_status: models.EvaluationStatus,
    reason: str = Query(default=None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(_require_head_judge_or_admin),
):
    VALID = {models.EvaluationStatus.OPEN, models.EvaluationStatus.SUBMITTED, models.EvaluationStatus.LOCKED, models.EvaluationStatus.FINALIZED}
    if new_status not in VALID:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status. Must be one of: {[s.value for s in VALID]}")

    evaluation = _get_or_404(db, models.Evaluation, evaluation_id)
    old_status = evaluation.status

    if new_status == old_status:
        return {"id": evaluation.id, "status": evaluation.status, "changed": False}

    allowed = VALID_TRANSITIONS.get(old_status, set())
    if new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition from {old_status.value if hasattr(old_status, 'value') else old_status} to {new_status.value if hasattr(new_status, 'value') else new_status}",
        )

    is_reopen = (old_status == models.EvaluationStatus.FINALIZED and new_status == models.EvaluationStatus.OPEN)
    if is_reopen and current_user.role.value not in ("HEAD_JUDGE", "ADMIN"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Head Judge or Admin can reopen a finalized evaluation")
    if is_reopen and (not reason or not reason.strip()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reason required to reopen a finalized evaluation")

    evaluation.status = new_status
    db.add(evaluation)
    db.flush()

    try:
        action = f"evaluation_{new_status.lower()}"
        _audit_log(
            db, current_user, action, 'Evaluation', evaluation.id,
            old_value=old_status, new_value=new_status,
            reason=reason.strip() if reason else None,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"id": evaluation.id, "status": evaluation.status, "changed": True}


# ─── Audit log for a specific evaluation ──────────────────────────────────────

@router.get("/evaluations/{evaluation_id}/audit")
def get_evaluation_audit(
    evaluation_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(_require_head_judge_or_admin),
):
    evaluation = _get_or_404(db, models.Evaluation, evaluation_id)
    logs = db.query(models.AuditLog).filter(
        models.AuditLog.entity_type == 'Evaluation',
        models.AuditLog.entity_id == evaluation_id,
    ).order_by(models.AuditLog.timestamp).all()
    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "actor_role": log.actor_role,
            "action": log.action,
            "old_value": log.old_value,
            "new_value": log.new_value,
            "reason": log.reason,
            "timestamp": log.timestamp,
        }
        for log in logs
    ]


# ─── List my evaluations ───────────────────────────────────────────────────────

@router.get("/evaluations")
def list_my_evaluations(
    comp_id: int = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(_require_judge_or_head),
):
    judge = db.query(models.Judge).filter(models.Judge.user_id == current_user.id).first()
    if not judge:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not a judge")
    query = db.query(models.Evaluation).filter(models.Evaluation.judge_id == judge.id)
    if comp_id is not None:
        query = query.filter(models.Evaluation.competition_id == comp_id)
    evals = query.all()
    return [
        {
            "id": e.id,
            "team_id": e.team_id,
            "competition_id": e.competition_id,
            "status": e.status,
            "created_at": e.created_at,
            "scores": [
                {
                    "criterion": s.criterion.name if s.criterion else None,
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
    current_user: models.User = Depends(_require_judge_or_head),
):
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
    current_user: models.User = Depends(_require_judge_or_head),
):
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
