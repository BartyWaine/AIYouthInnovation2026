from datetime import datetime
import os
import hashlib
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import SessionLocal
from .. import models
from ..security import get_current_user, require_role

router = APIRouter(prefix="/deliverables", tags=["submissions"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
ALLOWED_EXTENSIONS = {".docx", ".pdf", ".pptx", ".zip", ".mp4", ".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB per file


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _authorize_submission_access(db: Session, user: models.User, submission: models.Submission):
    """Enforce that a user may only access submissions they are entitled to.

    - ADMIN: full access (oversight)
    - TEAM_MEMBER: only their own team's submissions
    - JUDGE: only teams they are assigned to
    """
    role = user.role.value
    if role == "ADMIN":
        return
    if role == "TEAM_MEMBER":
        member = db.query(models.TeamMember).filter(
            models.TeamMember.team_id == submission.team_id,
            models.TeamMember.user_id == user.id,
        ).first()
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this submission",
            )
        return
    if role == "JUDGE":
        judge = db.query(models.Judge).filter(models.Judge.user_id == user.id).first()
        if not judge:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this submission",
            )
        assignment = db.query(models.JudgeAssignment).filter(
            models.JudgeAssignment.judge_id == judge.id,
            models.JudgeAssignment.team_id == submission.team_id,
        ).first()
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Judge not assigned to this team",
            )
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized to access this submission",
    )


def _parse_deadline(value: str = None):
    if not value:
        return None
    return datetime.fromisoformat(value)


@router.post("/standard")
def create_standard_deliverables(
    competition_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role('ADMIN')),
):
    """Create the six standard deliverable categories for a competition.

    Idempotent: categories already present for this competition are skipped.
    Each deliverable gives every team a space to upload the corresponding file.
    """
    if db.get(models.Competition, competition_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competition not found")

    existing = {
        d.category
        for d in db.query(models.Deliverable)
        .filter(models.Deliverable.competition_id == competition_id)
        .all()
        if d.category is not None
    }

    created = []
    for category in models.DeliverableCategory:
        if category.value in existing:
            continue
        deliverable = models.Deliverable(
            competition_id=competition_id,
            name=category.value,
            category=category,
        )
        db.add(deliverable)
        created.append(category.value)
    db.commit()
    return {"created": created, "standard_deliverables": models.STANDARD_DELIVERABLES}


@router.get("")
def list_deliverables(
    competition_id: int = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.Deliverable)
    if competition_id is not None:
        query = query.filter(models.Deliverable.competition_id == competition_id)
    return query.all()


@router.post("")
def create_deliverable(
    competition_id: int,
    name: str,
    description: str = None,
    deadline: str = None,
    required_file_types: str = None,
    max_file_size: int = None,
    category: models.DeliverableCategory = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role('ADMIN')),
):
    if db.get(models.Competition, competition_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competition not found")
    deliverable = models.Deliverable(
        competition_id=competition_id,
        name=name,
        category=category,
        description=description,
        deadline=_parse_deadline(deadline),
        required_file_types=required_file_types,
        max_file_size=max_file_size,
    )
    db.add(deliverable)
    db.commit()
    db.refresh(deliverable)
    # Audit log for deliverable creation
    audit = models.AuditLog(
        user_id=current_user.id,
        action='create_deliverable',
        entity_type='Deliverable',
        entity_id=deliverable.id,
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return {"id": deliverable.id, "name": deliverable.name, "category": deliverable.category}


@router.get("/{deliverable_id}/submissions")
def list_submissions(
    deliverable_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    submissions = db.query(models.Submission).filter(models.Submission.deliverable_id == deliverable_id).all()
    result = []
    for sub in submissions:
        team = db.get(models.Team, sub.team_id)
        result.append({
            "id": sub.id,
            "deliverable_id": sub.deliverable_id,
            "team_id": sub.team_id,
            "team_name": team.name if team else None,
            "version": sub.version,
            "status": sub.status.value,
            "created_at": sub.created_at,
            "updated_at": sub.updated_at,
        })
    return result


@router.post("/{deliverable_id}/submissions")
def create_submission(
    deliverable_id: int,
    team_id: int,
    version: int = 1,
    submission_status: str = "OPEN",
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role('TEAM_MEMBER')),
):
    if submission_status not in models.SubmissionStatus.__members__:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")
    if db.get(models.Deliverable, deliverable_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deliverable not found")
    # Verify current user is a member of the team
    team_member = db.query(models.TeamMember).filter(
        models.TeamMember.team_id == team_id,
        models.TeamMember.user_id == current_user.id
    ).first()
    if not team_member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not a member of the specified team")

    submission = models.Submission(
        deliverable_id=deliverable_id,
        team_id=team_id,
        version=version,
        status=models.SubmissionStatus[submission_status],
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    # Log audit record for submission creation
    audit = models.AuditLog(
        user_id=current_user.id,
        action='create_submission',
        entity_type='Submission',
        entity_id=submission.id,
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)

    return {
        "id": submission.id,
        "deliverable_id": submission.deliverable_id,
        "team_id": submission.team_id,
        "status": submission.status.value,
    }


@router.post("/submissions/{submission_id}/files")
def add_file(
    submission_id: int,
    file: UploadFile = File(...),
    version: int = Form(1),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role('TEAM_MEMBER')),
):
    submission = db.get(models.Submission, submission_id)
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    team_member = db.query(models.TeamMember).filter(
        models.TeamMember.team_id == submission.team_id,
        models.TeamMember.user_id == current_user.id,
    ).first()
    if not team_member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not part of the submission's team")

    filename = file.filename or "upload"
    _, ext = os.path.splitext(filename)
    ext_lower = ext.lower()
    if ext_lower not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{ext_lower}' not allowed. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    content = file.file.read()
    file_size = len(content)
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB",
        )

    checksum = hashlib.sha256(content).hexdigest()

    deliverable = db.get(models.Deliverable, submission.deliverable_id)
    comp_id = deliverable.competition_id if deliverable else "unknown"
    team_id = submission.team_id

    file_uuid = uuid.uuid4().hex
    subdir = os.path.join(UPLOAD_DIR, f"comp_{comp_id}", f"team_{team_id}", f"deliverable_{submission.deliverable_id}")
    os.makedirs(subdir, exist_ok=True)
    stored_name = f"{file_uuid}{ext_lower}"
    storage_path = os.path.join(subdir, stored_name)
    with open(storage_path, "wb") as f:
        f.write(content)

    old_files = db.query(models.SubmissionFile).filter(models.SubmissionFile.submission_id == submission_id).all()
    for old in old_files:
        try:
            if os.path.exists(old.storage_path):
                os.remove(old.storage_path)
        except OSError:
            pass
        db.delete(old)

    new_version = (version or 1)
    if old_files:
        latest = max(f.version for f in old_files)
        new_version = latest + 1

    db_file = models.SubmissionFile(
        submission_id=submission_id,
        original_filename=filename,
        storage_path=storage_path,
        file_type=file.content_type or ext_lower,
        file_size=file_size,
        checksum=checksum,
        version=new_version,
        submitted_at=datetime.utcnow(),
    )
    db.add(db_file)
    submission.status = models.SubmissionStatus.UPLOADED
    db.commit()
    db.refresh(db_file)
    return {
        "id": db_file.id,
        "submission_id": db_file.submission_id,
        "original_filename": db_file.original_filename,
        "file_type": db_file.file_type,
        "file_size": db_file.file_size,
        "checksum": db_file.checksum,
        "version": db_file.version,
        "uploaded_at": db_file.uploaded_at,
        "submitted_at": db_file.submitted_at,
    }


@router.get("/submissions/{submission_id}/files")
def list_files(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    submission = db.get(models.Submission, submission_id)
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    _authorize_submission_access(db, current_user, submission)
    files = db.query(models.SubmissionFile).filter(models.SubmissionFile.submission_id == submission_id).all()
    return [
        {
            "id": f.id,
            "submission_id": f.submission_id,
            "original_filename": f.original_filename,
            "file_type": f.file_type,
            "file_size": f.file_size,
            "uploaded_at": f.uploaded_at,
            "submitted_at": f.submitted_at,
            "version": f.version,
        }
        for f in files
    ]


@router.get("/submissions/{submission_id}/files/{file_id}/download")
def download_file(
    submission_id: int,
    file_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    submission = db.get(models.Submission, submission_id)
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    _authorize_submission_access(db, current_user, submission)
    file_record = db.query(models.SubmissionFile).filter(
        models.SubmissionFile.id == file_id,
        models.SubmissionFile.submission_id == submission_id,
    ).first()
    if not file_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    if not os.path.isfile(file_record.storage_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on storage")
    return FileResponse(
        path=file_record.storage_path,
        filename=file_record.original_filename,
        media_type=file_record.file_type or "application/octet-stream",
    )


@router.get("/competitions/{competition_id}/submissions")
def list_competition_submissions(
    competition_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role('JUDGE')),
):
    """List all submissions (with files) for all teams in a competition that the judge is assigned to."""
    judge = db.query(models.Judge).filter(models.Judge.user_id == current_user.id).first()
    if not judge:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not a judge")
    assigned_team_ids = [
        ja.team_id for ja in db.query(models.JudgeAssignment).filter(
            models.JudgeAssignment.judge_id == judge.id,
            models.JudgeAssignment.competition_id == competition_id,
        ).all()
    ]
    if not assigned_team_ids:
        return []
    submissions = db.query(models.Submission).join(models.Deliverable).filter(
        models.Deliverable.competition_id == competition_id,
        models.Submission.team_id.in_(assigned_team_ids),
    ).all()
    result = []
    for sub in submissions:
        team = db.get(models.Team, sub.team_id)
        deliverable = db.get(models.Deliverable, sub.deliverable_id)
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
            "competition_id": competition_id,
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


@router.patch("/submissions/{submission_id}/status")
def update_submission_status(
    submission_id: int,
    new_status: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role('TEAM_MEMBER')),
):
    # Verify submission exists
    submission = db.get(models.Submission, submission_id)
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    # Verify user belongs to the team of the submission
    team_member = db.query(models.TeamMember).filter(
        models.TeamMember.team_id == submission.team_id,
        models.TeamMember.user_id == current_user.id,
    ).first()
    if not team_member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not part of the submission's team")
    # Validate status
    if new_status not in models.SubmissionStatus.__members__:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")
    # Update status
    submission.status = models.SubmissionStatus[new_status]
    db.commit()
    db.refresh(submission)
    # Audit log for status change
    audit = models.AuditLog(
        user_id=current_user.id,
        action='update_submission_status',
        entity_type='Submission',
        entity_id=submission.id,
        metadata_json={"old_status": submission.status.value, "new_status": new_status},
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return {"id": submission.id, "status": submission.status.value}

