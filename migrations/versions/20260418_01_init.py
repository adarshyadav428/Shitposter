"""init schema

Revision ID: 20260418_01
Revises:
Create Date: 2026-04-18
"""
from alembic import op
import sqlalchemy as sa

revision = "20260418_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sources",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("family", sa.String(64), index=True),
        sa.Column("tier", sa.Integer, nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("sector", sa.String(32), index=True),
        sa.Column("rep_alpha", sa.Float, server_default="4.0"),
        sa.Column("rep_beta", sa.Float, server_default="1.0"),
        sa.Column("active", sa.Boolean, server_default=sa.true()),
        sa.Column("cooldown_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "canonical_events",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("sector", sa.String(32), index=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("entities", sa.JSON, nullable=False),
        sa.Column("confidence", sa.Float, server_default="0"),
        sa.Column("state", sa.String(24), server_default="pending", index=True),
        sa.Column("drop_reason", sa.String(64), nullable=True),
        sa.Column("draft", sa.Text, nullable=True),
        sa.Column("claims", sa.JSON, nullable=True),
        sa.Column("retracted", sa.Boolean, server_default=sa.false()),
        sa.Column("retracted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "raw_items",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("source_id", sa.String(64), sa.ForeignKey("sources.id"), index=True),
        sa.Column("external_id", sa.String(256), nullable=False),
        sa.Column("url", sa.Text, nullable=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("simhash", sa.BigInteger, nullable=False),
        sa.Column("seen_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("payload", sa.JSON, nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("canonical_event_id", sa.Integer, sa.ForeignKey("canonical_events.id"), nullable=True, index=True),
        sa.UniqueConstraint("source_id", "external_id", name="uq_source_external"),
    )
    op.create_table(
        "publications",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("event_id", sa.Integer, sa.ForeignKey("canonical_events.id"), index=True),
        sa.Column("channel", sa.String(24), nullable=False),
        sa.Column("external_id", sa.String(128), nullable=True),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("posted_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("corrected", sa.Boolean, server_default=sa.false()),
        sa.UniqueConstraint("event_id", "channel", name="uq_event_channel"),
    )
    op.create_index("ix_pub_channel_ts", "publications", ["channel", "posted_at"])
    op.create_table(
        "rate_budgets",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used", sa.Integer, server_default="0"),
        sa.Column("cap", sa.Integer, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("rate_budgets")
    op.drop_index("ix_pub_channel_ts", table_name="publications")
    op.drop_table("publications")
    op.drop_table("raw_items")
    op.drop_table("canonical_events")
    op.drop_table("sources")
