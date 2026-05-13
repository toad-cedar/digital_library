"""add_casbin_rule_table

Revision ID: 6a3fddcd6998
Revises: 811c3e623d7d
Create Date: 2026-05-13 21:02:49.065720

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6a3fddcd6998'
down_revision: Union[str, Sequence[str], None] = '811c3e623d7d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
  """Upgrade schema."""
  op.create_table(
    'casbin_rule',
    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('ptype', sa.String(255)),
    sa.Column('v0', sa.String(255)),
    sa.Column('v1', sa.String(255)),
    sa.Column('v2', sa.String(255)),
    sa.Column('v3', sa.String(255)),
    sa.Column('v4', sa.String(255)),
    sa.Column('v5', sa.String(255)),
  )
  op.create_index('ix_casbin_rule_ptype', 'casbin_rule', ['ptype'])


def downgrade() -> None:
  """Downgrade schema."""
  op.drop_index('ix_casbin_rule_ptype')
  op.drop_table('casbin_rule')
