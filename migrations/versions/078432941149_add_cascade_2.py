"""add cascade 2

Revision ID: 078432941149
Revises: ee405289e1f0
Create Date: 2025-08-02 00:43:41.759717
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '078432941149'
down_revision: Union[str, Sequence[str], None] = 'ee405289e1f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    
    op.drop_constraint('students_user_id_fkey', 'students', type_='foreignkey')
    op.create_foreign_key(
        'students_user_id_fkey',
        'students',
        'users',
        ['user_id'],
        ['userid'],
        ondelete='CASCADE'
    )

    
    op.drop_constraint('counselors_user_id_fkey', 'counselors', type_='foreignkey')
    op.create_foreign_key(
        'counselors_user_id_fkey',
        'counselors',
        'users',
        ['user_id'],
        ['userid'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    

    op.drop_constraint('students_user_id_fkey', 'students', type_='foreignkey')
    op.create_foreign_key(
        'students_user_id_fkey',
        'students',
        'users',
        ['user_id'],
        ['userid']
    )

    op.drop_constraint('counselors_user_id_fkey', 'counselors', type_='foreignkey')
    op.create_foreign_key(
        'counselors_user_id_fkey',
        'counselors',
        'users',
        ['user_id'],
        ['userid']
    )
