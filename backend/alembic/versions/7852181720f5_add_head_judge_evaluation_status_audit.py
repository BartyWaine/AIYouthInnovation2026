"""add_head_judge_evaluation_status_audit

Revision ID: 7852181720f5
Revises: 20260818000001
Create Date: 2026-08-28 23:47:00.221234

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7852181720f5'
down_revision: Union[str, None] = '20260818000001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('audit_logs', sa.Column('actor_role', sa.String(length=20), nullable=True))
    op.add_column('audit_logs', sa.Column('target_judge_id', sa.Integer(), nullable=True))
    op.add_column('audit_logs', sa.Column('old_value', sa.String(), nullable=True))
    op.add_column('audit_logs', sa.Column('new_value', sa.String(), nullable=True))
    op.add_column('audit_logs', sa.Column('reason', sa.Text(), nullable=True))
    op.add_column('evaluation_scores', sa.Column('corrected_by_user_id', sa.Integer(), nullable=True))
    op.add_column('evaluation_scores', sa.Column('corrected_at', sa.DateTime(), nullable=True))
    op.add_column('evaluations', sa.Column('status', sa.String(length=20), nullable=False, server_default='OPEN'))
    op.add_column('evaluations', sa.Column('updated_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('evaluations', 'updated_at')
    op.drop_column('evaluations', 'status')
    op.drop_column('evaluation_scores', 'corrected_at')
    op.drop_column('evaluation_scores', 'corrected_by_user_id')
    op.drop_column('audit_logs', 'reason')
    op.drop_column('audit_logs', 'new_value')
    op.drop_column('audit_logs', 'old_value')
    op.drop_column('audit_logs', 'target_judge_id')
    op.drop_column('audit_logs', 'actor_role')
