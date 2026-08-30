from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models
from ..security import get_current_user, require_role

router = APIRouter(prefix="/validation", tags=["validation"])

@router.post("/submissions/{submission_id}/validate")
def validate_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role('TEAM_MEMBER')),
):
    # Ensure the submission exists
    submission = db.get(models.Submission, submission_id)
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    # Mock AI validation – return a dummy result
    return {
        "submission_id": submission_id,
        "status": "VALID",
        "confidence": 0.97,
        "message": "AI validation passed (mock)"
    }
