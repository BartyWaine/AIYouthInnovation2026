from enum import Enum
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Enum as SqlEnum,
    ForeignKey,
    Text,
    Float,
    JSON,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship

from .database import Base


# ============================================================
# ENUMS
# ============================================================

class UserRole(str, Enum):
    TEAM_MEMBER = "TEAM_MEMBER"
    TEAM_LEADER = "TEAM_LEADER"
    ADMIN = "ADMIN"
    JUDGE = "JUDGE"
    LECTURER = "LECTURER"

class CompetitionCategory(str, Enum):
    ENGINEERING = "AI for Engineering and Technology"
    SOCIAL = "AI for Social Innovation"
    ENTREPRENEURSHIP = "AI for Entrepreneurship"



class SubmissionStatus(str, Enum):
    OPEN = "OPEN"
    UPLOADED = "UPLOADED"
    AI_CHECK = "AI_CHECK"
    NEED_REVISION = "NEED_REVISION"
    READY = "READY"
    SUBMITTED = "SUBMITTED"
    LOCKED = "LOCKED"


class DeliverableCategory(str, Enum):
    """Standard deliverable categories each team must upload for a competition."""
    PROBLEM_STATEMENT = "Problem statement & User personal"
    AI_SOLUTION = "AI driven solution & User persona"
    PROTOTYPE = "Functional prototype or mockup"
    PITCH_DECK = "Competition pitch deck"
    BUSINESS_MODEL = "Business model summary"
    IMPACT_SDG = "Impact & SDG alignment summary"


# The six standard deliverables every team gets upload space for.
STANDARD_DELIVERABLES = [c.value for c in DeliverableCategory]


# ============================================================
# USERS
# ============================================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False)

    email = Column(
        String,
        nullable=False,
        unique=True,
    )

    password_hash = Column(
        String,
        nullable=False,
    )

    role = Column(
        SqlEnum(UserRole),
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Relationships
    team_memberships = relationship(
        "TeamMember",
        back_populates="user",
    )

    judge = relationship(
        "Judge",
        uselist=False,
        back_populates="user",
    )

    audit_logs = relationship(
        "AuditLog",
        back_populates="user",
    )

    __table_args__ = (
        Index(
            "ix_users_email",
            "email",
            unique=True,
        ),
    )


# ============================================================
# COMPETITIONS
# ============================================================

class Competition(Base):
    __tablename__ = "competitions"

    id = Column(
        Integer,
        primary_key=True,
        nullable=False,
    )

    name = Column(
        String,
        nullable=False,
    )
    category = Column(
        String(33),
        nullable=False,
        default=CompetitionCategory.ENGINEERING,
    )

    start_date = Column(
        DateTime,
    )

    end_date = Column(
        DateTime,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Relationships
    teams = relationship(
        "Team",
        back_populates="competition",
    )

    deliverables = relationship(
        "Deliverable",
        back_populates="competition",
    )

    judge_assignments = relationship(
        "JudgeAssignment",
        back_populates="competition",
    )

    evaluations = relationship(
        "Evaluation",
        back_populates="competition",
    )


# ============================================================
# TEAMS
# ============================================================

class Team(Base):
    __tablename__ = "teams"

    id = Column(
        Integer,
        primary_key=True,
        nullable=False,
    )

    name = Column(
        String,
        nullable=False,
    )

    competition_id = Column(
        Integer,
        ForeignKey("competitions.id"),
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    competition = relationship(
        "Competition",
        back_populates="teams",
    )

    members = relationship(
        "TeamMember",
        back_populates="team",
    )

    submissions = relationship(
        "Submission",
        back_populates="team",
    )

    judge_assignments = relationship(
        "JudgeAssignment",
        back_populates="team",
    )

    __table_args__ = (
        Index(
            "ix_teams_competition_id",
            "competition_id",
        ),
    )


# ============================================================
# TEAM MEMBERS
# ============================================================

class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(
        Integer,
        primary_key=True,
        nullable=False,
    )

    team_id = Column(
        Integer,
        ForeignKey("teams.id"),
        nullable=False,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    is_leader = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    team = relationship(
        "Team",
        back_populates="members",
    )

    user = relationship(
        "User",
        back_populates="team_memberships",
    )

    __table_args__ = (
        UniqueConstraint(
            "team_id",
            "user_id",
            name="uq_team_user",
        ),
        Index(
            "ix_teammember_team_user",
            "team_id",
            "user_id",
        ),
    )


# ============================================================
# DELIVERABLES
# ============================================================

class Deliverable(Base):
    __tablename__ = "deliverables"

    id = Column(
        Integer,
        primary_key=True,
        nullable=False,
    )

    competition_id = Column(
        Integer,
        ForeignKey("competitions.id"),
        nullable=False,
    )

    name = Column(
        String,
        nullable=False,
    )

    category = Column(
        String(33),
        nullable=True,
    )

    description = Column(
        Text,
    )

    deadline = Column(
        DateTime,
    )

    required_file_types = Column(
        String,
    )

    max_file_size = Column(
        Integer,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    competition = relationship(
        "Competition",
        back_populates="deliverables",
    )

    submissions = relationship(
        "Submission",
        back_populates="deliverable",
    )

    __table_args__ = (
        Index(
            "ix_deliverables_competition_id",
            "competition_id",
        ),
    )


# ============================================================
# SUBMISSIONS
# ============================================================

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(
        Integer,
        primary_key=True,
        nullable=False,
    )

    deliverable_id = Column(
        Integer,
        ForeignKey("deliverables.id"),
        nullable=False,
    )

    team_id = Column(
        Integer,
        ForeignKey("teams.id"),
        nullable=False,
    )

    version = Column(
        Integer,
        nullable=False,
        default=1,
    )

    status = Column(
        SqlEnum(SubmissionStatus),
        nullable=False,
        default=SubmissionStatus.OPEN,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    deliverable = relationship(
        "Deliverable",
        back_populates="submissions",
    )

    team = relationship(
        "Team",
        back_populates="submissions",
    )

    files = relationship(
        "SubmissionFile",
        back_populates="submission",
    )

    __table_args__ = (
        Index(
            "ix_submissions_deliverable_id",
            "deliverable_id",
        ),
        Index(
            "ix_submissions_team_id",
            "team_id",
        ),
    )


# ============================================================
# SUBMISSION FILES
# ============================================================

class SubmissionFile(Base):
    __tablename__ = "submission_files"

    id = Column(
        Integer,
        primary_key=True,
        nullable=False,
    )

    submission_id = Column(
        Integer,
        ForeignKey("submissions.id"),
        nullable=False,
    )

    original_filename = Column(
        String,
        nullable=False,
    )

    storage_path = Column(
        String,
        nullable=False,
    )

    file_type = Column(
        String,
    )

    file_size = Column(
        Integer,
    )

    checksum = Column(
        String,
    )

    uploaded_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    submitted_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    version = Column(
        Integer,
        nullable=False,
        default=1,
    )

    submission = relationship(
        "Submission",
        back_populates="files",
    )

    __table_args__ = (
        Index(
            "ix_submissionfile_submission",
            "submission_id",
        ),
    )


# ============================================================
# JUDGES
# ============================================================

class Judge(Base):
    __tablename__ = "judges"

    id = Column(
        Integer,
        primary_key=True,
        nullable=False,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    user = relationship(
        "User",
        back_populates="judge",
    )

    assignments = relationship(
        "JudgeAssignment",
        back_populates="judge",
    )

    evaluations = relationship(
        "Evaluation",
        back_populates="judge",
    )


# ============================================================
# JUDGE ASSIGNMENTS
# ============================================================

class JudgeAssignment(Base):
    __tablename__ = "judge_assignments"

    id = Column(
        Integer,
        primary_key=True,
        nullable=False,
    )

    judge_id = Column(
        Integer,
        ForeignKey("judges.id"),
        nullable=False,
    )

    team_id = Column(
        Integer,
        ForeignKey("teams.id"),
        nullable=False,
    )

    competition_id = Column(
        Integer,
        ForeignKey("competitions.id"),
        nullable=False,
    )

    assigned_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    assigned_by = Column(
        Integer,
        ForeignKey("users.id"),
    )

    judge = relationship(
        "Judge",
        back_populates="assignments",
    )

    team = relationship(
        "Team",
        back_populates="judge_assignments",
    )

    competition = relationship(
        "Competition",
        back_populates="judge_assignments",
    )

    __table_args__ = (
        UniqueConstraint(
            "judge_id",
            "team_id",
            "competition_id",
            name="uq_judge_team_comp",
        ),
    )


# ============================================================
# EVALUATION CRITERIA
# ============================================================

class EvaluationCriteria(Base):
    __tablename__ = "evaluation_criteria"

    id = Column(
        Integer,
        primary_key=True,
        nullable=False,
    )

    name = Column(
        String,
        nullable=False,
    )

    weight = Column(
        Float,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "name",
            name="uq_criteria_name",
        ),
    )


# ============================================================
# EVALUATIONS
# ============================================================

class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(
        Integer,
        primary_key=True,
        nullable=False,
    )

    judge_id = Column(
        Integer,
        ForeignKey("judges.id"),
        nullable=False,
    )

    team_id = Column(
        Integer,
        ForeignKey("teams.id"),
        nullable=False,
    )

    competition_id = Column(
        Integer,
        ForeignKey("competitions.id"),
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    judge = relationship(
        "Judge",
        back_populates="evaluations",
    )

    team = relationship(
        "Team",
    )

    competition = relationship(
        "Competition",
        back_populates="evaluations",
    )

    scores = relationship(
        "EvaluationScore",
        back_populates="evaluation",
    )

    __table_args__ = (
        UniqueConstraint(
            "judge_id",
            "team_id",
            "competition_id",
            name="uq_evaluation_unique",
        ),
    )


# ============================================================
# EVALUATION SCORES
# ============================================================

class EvaluationScore(Base):
    __tablename__ = "evaluation_scores"

    id = Column(
        Integer,
        primary_key=True,
        nullable=False,
    )

    evaluation_id = Column(
        Integer,
        ForeignKey("evaluations.id"),
        nullable=False,
    )

    criterion_id = Column(
        Integer,
        ForeignKey("evaluation_criteria.id"),
        nullable=False,
    )

    score = Column(
        Float,
        nullable=False,
    )

    comment = Column(
        Text,
    )

    evaluation = relationship(
        "Evaluation",
        back_populates="scores",
    )

    criterion = relationship(
        "EvaluationCriteria",
    )

    __table_args__ = (
        UniqueConstraint(
            "evaluation_id",
            "criterion_id",
            name="uq_eval_score_criterion",
        ),
    )


# ============================================================
# AUDIT LOGS
# ============================================================

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(
        Integer,
        primary_key=True,
        nullable=False,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    action = Column(
        String,
        nullable=False,
    )

    entity_type = Column(
        String,
    )

    entity_id = Column(
        Integer,
    )

    timestamp = Column(
        DateTime,
        default=datetime.utcnow,
    )

    ip_address = Column(
        String,
    )

    # JSON (portable across SQLite and PostgreSQL)
    metadata_json = Column(
        JSON,
        nullable=True,
    )

    user = relationship(
        "User",
        back_populates="audit_logs",
    )