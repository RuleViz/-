"""add resume match delivery pipeline tables

Revision ID: 20260220_0001
Revises: 
Create Date: 2026-02-20 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260220_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "resumes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.String(length=100), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.String(length=1024), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="uploaded"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_resumes_user_id", "resumes", ["user_id"])

    op.create_table(
        "resume_parses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("resume_id", sa.Integer(), sa.ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parsed_json", sa.JSON(), nullable=True),
        sa.Column("extracted_fields", sa.JSON(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("parsed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_resume_parses_resume_id", "resume_parses", ["resume_id"])

    op.create_table(
        "match_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("resume_id", sa.Integer(), sa.ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("reason_snippet", sa.Text(), nullable=True),
        sa.Column("highlights", sa.JSON(), nullable=True),
        sa.Column("template_recommendation", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_match_results_resume_id", "match_results", ["resume_id"])
    op.create_index("ix_match_results_job_id", "match_results", ["job_id"])

    op.create_table(
        "delivery_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.String(length=100), nullable=False),
        sa.Column("resume_id", sa.Integer(), sa.ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("job_ids", sa.JSON(), nullable=False),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="created"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_delivery_jobs_user_id", "delivery_jobs", ["user_id"])
    op.create_index("ix_delivery_jobs_resume_id", "delivery_jobs", ["resume_id"])

    op.create_table(
        "delivery_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("delivery_job_id", sa.Integer(), sa.ForeignKey("delivery_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resume_id", sa.Integer(), sa.ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("simulated_status", sa.String(length=50), nullable=False, server_default="queued"),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("template_name", sa.String(length=100), nullable=True),
        sa.Column("attachment_names", sa.JSON(), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
    )
    op.create_index("ix_delivery_logs_delivery_job_id", "delivery_logs", ["delivery_job_id"])
    op.create_index("ix_delivery_logs_job_id", "delivery_logs", ["job_id"])
    op.create_index("ix_delivery_logs_resume_id", "delivery_logs", ["resume_id"])
    op.create_index("ix_delivery_logs_simulated_status", "delivery_logs", ["simulated_status"])
    op.create_index("ix_delivery_logs_timestamp", "delivery_logs", ["timestamp"])


def downgrade() -> None:
    op.drop_index("ix_delivery_logs_timestamp", table_name="delivery_logs")
    op.drop_index("ix_delivery_logs_simulated_status", table_name="delivery_logs")
    op.drop_index("ix_delivery_logs_resume_id", table_name="delivery_logs")
    op.drop_index("ix_delivery_logs_job_id", table_name="delivery_logs")
    op.drop_index("ix_delivery_logs_delivery_job_id", table_name="delivery_logs")
    op.drop_table("delivery_logs")

    op.drop_index("ix_delivery_jobs_resume_id", table_name="delivery_jobs")
    op.drop_index("ix_delivery_jobs_user_id", table_name="delivery_jobs")
    op.drop_table("delivery_jobs")

    op.drop_index("ix_match_results_job_id", table_name="match_results")
    op.drop_index("ix_match_results_resume_id", table_name="match_results")
    op.drop_table("match_results")

    op.drop_index("ix_resume_parses_resume_id", table_name="resume_parses")
    op.drop_table("resume_parses")

    op.drop_index("ix_resumes_user_id", table_name="resumes")
    op.drop_table("resumes")
