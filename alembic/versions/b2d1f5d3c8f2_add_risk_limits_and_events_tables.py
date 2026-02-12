"""add_risk_limits_and_events_tables

Revision ID: b2d1f5d3c8f2
Revises: a2ff27f734f9
Create Date: 2025-12-26 01:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "b2d1f5d3c8f2"
down_revision: Union[str, None] = "a2ff27f734f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = inspector.get_table_names()

    if "risk_limits" not in existing_tables:
        op.create_table(
            "risk_limits",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("strategy_id", sa.String(length=36), nullable=True),
            sa.Column("daily_loss_inr", sa.Numeric(18, 6), nullable=True),
            sa.Column("daily_loss_pct", sa.Numeric(18, 6), nullable=True),
            sa.Column("max_position_value_inr", sa.Numeric(18, 6), nullable=True),
            sa.Column("max_position_qty", sa.Integer(), nullable=True),
            sa.Column("max_gross_exposure_inr", sa.Numeric(18, 6), nullable=True),
            sa.Column("max_net_exposure_inr", sa.Numeric(18, 6), nullable=True),
            sa.Column("max_open_orders", sa.Integer(), nullable=True),
            sa.Column("cutoff_time", sa.String(length=5), nullable=True),
            sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("is_halted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("halted_reason", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), onupdate=sa.func.now()),
        )
        op.create_index("ix_risk_limits_user_strategy", "risk_limits", ["user_id", "strategy_id"])
    else:
        columns = {col["name"] for col in inspector.get_columns("risk_limits")}
        additions = [
            ("strategy_id", sa.Column("strategy_id", sa.String(length=36), nullable=True)),
            ("daily_loss_inr", sa.Column("daily_loss_inr", sa.Numeric(18, 6), nullable=True)),
            ("daily_loss_pct", sa.Column("daily_loss_pct", sa.Numeric(18, 6), nullable=True)),
            ("max_position_value_inr", sa.Column("max_position_value_inr", sa.Numeric(18, 6), nullable=True)),
            ("max_position_qty", sa.Column("max_position_qty", sa.Integer(), nullable=True)),
            ("max_gross_exposure_inr", sa.Column("max_gross_exposure_inr", sa.Numeric(18, 6), nullable=True)),
            ("max_net_exposure_inr", sa.Column("max_net_exposure_inr", sa.Numeric(18, 6), nullable=True)),
            ("max_open_orders", sa.Column("max_open_orders", sa.Integer(), nullable=True)),
            ("cutoff_time", sa.Column("cutoff_time", sa.String(length=5), nullable=True)),
            ("is_enabled", sa.Column("is_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False)),
            ("is_halted", sa.Column("is_halted", sa.Boolean(), server_default=sa.text("false"), nullable=False)),
            ("halted_reason", sa.Column("halted_reason", sa.Text(), nullable=True)),
            ("updated_at", sa.Column("updated_at", sa.DateTime(), onupdate=sa.func.now())),
        ]
        for name, column in additions:
            if name not in columns:
                op.add_column("risk_limits", column)
        indexes = {idx["name"] for idx in inspector.get_indexes("risk_limits")}
        if "ix_risk_limits_user_strategy" not in indexes:
            op.create_index("ix_risk_limits_user_strategy", "risk_limits", ["user_id", "strategy_id"])

    if "risk_events" not in existing_tables:
        op.create_table(
            "risk_events",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("ts", sa.DateTime(), server_default=sa.func.now(), index=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("account_id", sa.Integer(), sa.ForeignKey("accounts.id"), nullable=True),
            sa.Column("strategy_id", sa.String(length=36), nullable=True),
            sa.Column("symbol", sa.String(length=50), nullable=True),
            sa.Column("event_type", sa.String(length=50), nullable=False),
            sa.Column("reason_code", sa.String(length=100), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("snapshot", sa.JSON(), nullable=True),
        )
        op.create_index("ix_risk_events_user_ts", "risk_events", ["user_id", "ts"])
    else:
        columns = {col["name"] for col in inspector.get_columns("risk_events")}
        if "ts" not in columns:
            op.add_column("risk_events", sa.Column("ts", sa.DateTime(), server_default=sa.func.now()))
        for col_name, column in [
            ("strategy_id", sa.Column("strategy_id", sa.String(length=36), nullable=True)),
            ("snapshot", sa.Column("snapshot", sa.JSON(), nullable=True)),
            ("symbol", sa.Column("symbol", sa.String(length=50), nullable=True)),
        ]:
            if col_name not in columns:
                op.add_column("risk_events", column)
        indexes = {idx["name"] for idx in inspector.get_indexes("risk_events")}
        if "ix_risk_events_user_ts" not in indexes:
            op.create_index("ix_risk_events_user_ts", "risk_events", ["user_id", "ts"])


def downgrade() -> None:
    op.drop_index("ix_risk_events_user_ts", table_name="risk_events")
    op.drop_index("ix_risk_limits_user_strategy", table_name="risk_limits")
    op.drop_table("risk_events")
    op.drop_table("risk_limits")
