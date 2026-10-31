# SPDX-License-Identifier: Apache-2.0
"""Add immutable, hash-bearing snapshot records.

Revision ID: 20261031_0005
Revises: 20261030_0004
"""

import sqlalchemy as sa
from alembic import op

revision = "20261031_0005"
down_revision = "20261030_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "snapshots",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("path", sa.String(length=2048), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.CheckConstraint("length(sha256) = 64", name="ck_snapshots_sha256_length"),
    )
    op.create_index("ix_snapshots_sha256", "snapshots", ["sha256"])


def downgrade() -> None:
    op.drop_index("ix_snapshots_sha256", table_name="snapshots")
    op.drop_table("snapshots")
