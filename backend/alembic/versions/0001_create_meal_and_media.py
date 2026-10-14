"""create meal and media_object

Revision ID: 0001
Revises:
Create Date: 2026-10-14
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

meal_type = sa.Enum("breakfast", "lunch", "dinner", "snack", "late_snack", "drink", name="meal_type")
media_kind = sa.Enum("source", "display", "ai", "thumb", name="media_kind")


def upgrade() -> None:
    op.create_table(
        "meal",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("request_id", sa.String(80), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("meal_type", meal_type, nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "request_id"),
    )
    op.create_index("ix_meal_user_captured", "meal", ["user_id", "captured_at", "id"])

    op.create_table(
        "media_object",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("meal_id", sa.Uuid(), sa.ForeignKey("meal.id"), nullable=False),
        sa.Column("kind", media_kind, nullable=False),
        sa.Column("processor_version", sa.Integer(), nullable=False),
        sa.Column("object_key", sa.Text(), nullable=False, unique=True),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("byte_size", sa.BigInteger(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("meal_id", "kind", "processor_version"),
        sa.CheckConstraint("byte_size > 0 AND width > 0 AND height > 0", name="positive_size"),
    )


def downgrade() -> None:
    op.drop_table("media_object")
    op.drop_index("ix_meal_user_captured", table_name="meal")
    op.drop_table("meal")
    media_kind.drop(op.get_bind())
    meal_type.drop(op.get_bind())
