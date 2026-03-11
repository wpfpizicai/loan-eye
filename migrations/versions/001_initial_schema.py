"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### competitors table ###
    op.create_table(
        'competitors',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('keywords', sa.ARRAY(sa.String()), nullable=False),
        sa.Column('category', sa.Enum('core', 'industry', name='competitorcategory'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # ### notes table ###
    op.create_table(
        'notes',
        sa.Column('note_id', sa.String(length=100), nullable=False),
        sa.Column('competitor_id', sa.String(), sa.ForeignKey('competitors.id'), nullable=True),
        sa.Column('keyword', sa.String(length=100), nullable=False),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('author', sa.String(length=100), nullable=True),
        sa.Column('publish_time', sa.DateTime(), nullable=True),
        sa.Column('likes', sa.Integer(), nullable=True),
        sa.Column('comments', sa.Integer(), nullable=True),
        sa.Column('collects', sa.Integer(), nullable=True),
        sa.Column('shares', sa.Integer(), nullable=True),
        sa.Column('is_hot', sa.Boolean(), nullable=True),
        sa.Column('url', sa.String(length=500), nullable=True),
        sa.Column('scraped_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('note_id'),
    )

    # ### comments table ###
    op.create_table(
        'comments',
        sa.Column('comment_id', sa.String(length=100), nullable=False),
        sa.Column('note_id', sa.String(length=100), sa.ForeignKey('notes.note_id'), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('author', sa.String(length=100), nullable=True),
        sa.Column('likes', sa.Integer(), nullable=True),
        sa.Column('publish_time', sa.DateTime(), nullable=True),
        sa.Column('sentiment_label', sa.Enum('positive', 'negative', 'neutral', name='sentimentlabel'), nullable=True),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('scraped_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('comment_id'),
    )

    # ### analysis_results table ###
    op.create_table(
        'analysis_results',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('competitor_id', sa.String(), sa.ForeignKey('competitors.id'), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('note_count', sa.Integer(), nullable=True),
        sa.Column('total_engagement', sa.Integer(), nullable=True),
        sa.Column('sentiment_positive_rate', sa.Float(), nullable=True),
        sa.Column('top_complaints', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('top_praises', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('product_features', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('hot_notes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('analysis_results')
    op.drop_table('comments')
    op.drop_table('notes')
    op.drop_table('competitors')
    op.execute('DROP TYPE IF EXISTS competitorcategory')
    op.execute('DROP TYPE IF EXISTS sentimentlabel')
