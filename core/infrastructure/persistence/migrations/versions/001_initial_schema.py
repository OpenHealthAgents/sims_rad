"""001_initial_schema

Initial migration creating patients, studies, work_items, reports,
report_versions (with append-only trigger), report_deliveries,
audit_events, and outbox_events tables.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-11-24 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. patients table
    op.create_table(
        "patients",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("mrn", sa.String(64), nullable=False),
        sa.Column("identifier_namespace", sa.String(255), nullable=False),
        sa.Column("reconciliation_status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("family_name", sa.String(128), nullable=True),
        sa.Column("given_name", sa.String(128), nullable=True),
        sa.Column("birth_date", sa.String(32), nullable=True),
        sa.Column("gender", sa.String(16), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_patients_mrn", "patients", ["mrn"], unique=True)

    # 2. studies table
    op.create_table(
        "studies",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("study_instance_uid", sa.String(64), nullable=False),
        sa.Column("accession_number", sa.String(64), nullable=False),
        sa.Column("patient_id", sa.String(64), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("modality", sa.String(16), nullable=False),
        sa.Column("study_date", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("source_system", sa.String(64), nullable=False, server_default="PACS-DEFAULT"),
        sa.Column("description", sa.String(255), nullable=False, server_default=""),
        sa.Column("priority", sa.String(16), nullable=False, server_default="ROUTINE"),
        sa.Column("state", sa.String(32), nullable=False, server_default="received"),
        sa.Column("storage_path", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_studies_study_instance_uid", "studies", ["study_instance_uid"], unique=True)
    op.create_index("ix_studies_accession_number", "studies", ["accession_number"], unique=True)
    op.create_index("ix_studies_patient_id", "studies", ["patient_id"])
    op.create_index("ix_studies_modality", "studies", ["modality"])
    op.create_index("ix_studies_priority", "studies", ["priority"])
    op.create_index("ix_studies_state", "studies", ["state"])

    # 3. work_items table
    op.create_table(
        "work_items",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("study_id", sa.String(64), sa.ForeignKey("studies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("state", sa.String(32), nullable=False, server_default="received"),
        sa.Column("priority", sa.String(16), nullable=False, server_default="ROUTINE"),
        sa.Column("assigned_radiologist_id", sa.String(64), nullable=True),
        sa.Column("sla_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_work_items_study_id", "work_items", ["study_id"])
    op.create_index("ix_work_items_state", "work_items", ["state"])
    op.create_index("ix_work_items_priority", "work_items", ["priority"])
    op.create_index("ix_work_items_assigned_radiologist_id", "work_items", ["assigned_radiologist_id"])
    op.create_index("ix_work_items_sla_deadline", "work_items", ["sla_deadline"])

    # 4. reports table
    op.create_table(
        "reports",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("work_item_id", sa.String(64), sa.ForeignKey("work_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("current_version_id", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_reports_work_item_id", "reports", ["work_item_id"], unique=True)
    op.create_index("ix_reports_status", "reports", ["status"])

    # 5. report_versions table (Append-Only)
    op.create_table(
        "report_versions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("report_id", sa.String(64), sa.ForeignKey("reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("structured_findings", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("impression", sa.Text(), nullable=False),
        sa.Column("author_id", sa.String(64), nullable=False),
        sa.Column("signature_hash", sa.String(128), nullable=True),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("report_id", "version_number", name="uq_report_version_number"),
    )
    op.create_index("ix_report_versions_report_id", "report_versions", ["report_id"])

    # Database-level trigger preventing UPDATE or DELETE on report_versions
    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_report_version_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'Table report_versions is strictly append-only. UPDATE and DELETE operations are forbidden.';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_report_versions_append_only
        BEFORE UPDATE OR DELETE ON report_versions
        FOR EACH ROW
        EXECUTE FUNCTION prevent_report_version_mutation();
        """
    )

    # 6. report_deliveries table
    op.create_table(
        "report_deliveries",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("report_id", sa.String(64), sa.ForeignKey("reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("destination_system", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("delivery_channel", sa.String(32), nullable=False, server_default="HL7_ORU_R01"),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_report_deliveries_report_id", "report_deliveries", ["report_id"])
    op.create_index("ix_report_deliveries_status", "report_deliveries", ["status"])

    # 7. audit_events table
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("actor_id", sa.String(64), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("resource_id", sa.String(64), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("correlation_id", sa.String(64), nullable=False, server_default=""),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_index("ix_audit_events_actor_id", "audit_events", ["actor_id"])
    op.create_index("ix_audit_events_action", "audit_events", ["action"])
    op.create_index("ix_audit_events_resource_id", "audit_events", ["resource_id"])
    op.create_index("ix_audit_events_timestamp", "audit_events", ["timestamp"])
    op.create_index("ix_audit_events_correlation_id", "audit_events", ["correlation_id"])

    # 8. outbox_events table
    op.create_table(
        "outbox_events",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("aggregate_type", sa.String(64), nullable=False),
        sa.Column("aggregate_id", sa.String(64), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_outbox_events_aggregate_type", "outbox_events", ["aggregate_type"])
    op.create_index("ix_outbox_events_aggregate_id", "outbox_events", ["aggregate_id"])
    op.create_index("ix_outbox_events_event_type", "outbox_events", ["event_type"])
    op.create_index("ix_outbox_events_created_at", "outbox_events", ["created_at"])
    op.create_index("ix_outbox_events_processed_at", "outbox_events", ["processed_at"])


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_report_versions_append_only ON report_versions;")
    op.execute("DROP FUNCTION IF EXISTS prevent_report_version_mutation();")
    op.drop_table("outbox_events")
    op.drop_table("audit_events")
    op.drop_table("report_deliveries")
    op.drop_table("report_versions")
    op.drop_table("reports")
    op.drop_table("work_items")
    op.drop_table("studies")
    op.drop_table("patients")
