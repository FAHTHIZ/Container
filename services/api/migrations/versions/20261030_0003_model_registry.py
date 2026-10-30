# SPDX-License-Identifier: Apache-2.0
"""Add project-scoped model registry and immutable version metadata.

Revision ID: 20261030_0003
Revises: 20261030_0002
"""

import sqlalchemy as sa
from alembic import op

revision = "20261030_0003"
down_revision = "20261030_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "registered_models",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("model_family", sa.String(length=120), nullable=True),
        sa.Column("origin", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("project_id", "name", name="uq_registered_models_project_name"),
    )
    op.create_index("ix_registered_models_workspace_id", "registered_models", ["workspace_id"])
    op.create_index("ix_registered_models_project_id", "registered_models", ["project_id"])
    op.create_index(
        "ix_registered_models_workspace_created",
        "registered_models",
        ["workspace_id", "created_at"],
    )

    op.create_table(
        "model_versions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("model_id", sa.String(length=36), nullable=False),
        sa.Column("artifact_id", sa.String(length=36), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=False),
        sa.Column("version_label", sa.String(length=80), nullable=False),
        sa.Column("format", sa.String(length=40), nullable=False),
        sa.Column("quantization", sa.String(length=80), nullable=True),
        sa.Column("source_uri", sa.String(length=2000), nullable=True),
        sa.Column("base_model_reference", sa.String(length=255), nullable=True),
        sa.Column("license_id", sa.String(length=120), nullable=True),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["model_id"], ["registered_models.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["artifact_id"], ["artifacts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("model_id", "version_label", name="uq_model_versions_label"),
    )
    op.create_index("ix_model_versions_model_id", "model_versions", ["model_id"])
    op.create_index("ix_model_versions_artifact_id", "model_versions", ["artifact_id"])
    op.create_index(
        "ix_model_versions_model_created", "model_versions", ["model_id", "created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_model_versions_model_created", table_name="model_versions")
    op.drop_index("ix_model_versions_artifact_id", table_name="model_versions")
    op.drop_index("ix_model_versions_model_id", table_name="model_versions")
    op.drop_table("model_versions")
    op.drop_index("ix_registered_models_workspace_created", table_name="registered_models")
    op.drop_index("ix_registered_models_project_id", table_name="registered_models")
    op.drop_index("ix_registered_models_workspace_id", table_name="registered_models")
    op.drop_table("registered_models")
