"""Add google_id to User model and initial table setup

Revision ID: 7d5ffa915c5d
Revises: 
Create Date: 2025-06-13 22:29:07.885198

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7d5ffa915c5d'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('google_id', sa.String(length=120), nullable=True))
        batch_op.create_unique_constraint("uq_user_google_id", ['google_id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='unique')
        batch_op.drop_column('google_id')

    # ### end Alembic commands ###
