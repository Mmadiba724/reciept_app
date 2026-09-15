"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-14

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "citext"')

    user_role = pg.ENUM(
        "owner", "admin", "staff",
        name="user_role",
        create_type=False,
    )

    receipt_status = pg.ENUM(
        "issued", "voided", "refunded",
        name="receipt_status",
        create_type=False,
    )

    delivery_channel = pg.ENUM(
        "email", "sms",
        name="delivery_channel",
        create_type=False,
    )

    delivery_status = pg.ENUM(
        "queued",
        "sent",
        "delivered",
        "bounced",
        "failed",
        "opened",
        name="delivery_status",
        create_type=False,
    )

    plan_tier = pg.ENUM(
        "free_trial",
        "starter",
        "growth",
        "enterprise",
        name="plan_tier",
        create_type=False,
    )

    payment_method_type = pg.ENUM(
        "cash",
        "bank_transfer",
        "mobile_money",
        "cheque",
        "other",
        name="payment_method_type",
        create_type=False,
    )

    bind = op.get_bind()
    for enum in (user_role, receipt_status, delivery_channel, delivery_status, plan_tier, payment_method_type):
        enum.create(bind, checkfirst=True)

    op.create_table(
        "tenants",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("business_name", sa.Text, nullable=False),
        sa.Column("logo_url", sa.Text),
        sa.Column("brand_color", sa.Text),
        sa.Column("po_box", sa.Text),
        sa.Column("physical_address", sa.Text),
        sa.Column("contact_phone", sa.Text),
        sa.Column("contact_email", sa.Text),
        sa.Column("bank_name", sa.Text),
        sa.Column("bank_account_number", sa.Text),
        sa.Column("plan_tier", plan_tier, nullable=False, server_default="free_trial"),
        sa.Column("default_currency", sa.CHAR(3), nullable=False, server_default="UGX"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "users",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", pg.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("full_name", sa.Text, nullable=False),
        sa.Column("email", pg.CITEXT, nullable=False),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("role", user_role, nullable=False, server_default="owner"),
        sa.Column("signature_image_url", sa.Text),
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("email_verification_token", sa.Text),
        sa.Column("password_reset_token", sa.Text),
        sa.Column("password_reset_expires_at", sa.DateTime(timezone=True)),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "email"),
    )
    op.create_index("idx_users_tenant", "users", ["tenant_id"])

    op.create_table(
        "customers",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", pg.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("email", pg.CITEXT),
        sa.Column("phone", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("email IS NOT NULL OR phone IS NOT NULL", name="chk_customer_has_contact"),
    )
    op.create_index("idx_customers_tenant", "customers", ["tenant_id"])
    op.create_index("idx_customers_email", "customers", ["tenant_id", "email"])
    op.create_index("idx_customers_phone", "customers", ["tenant_id", "phone"])

    op.create_table(
        "receipts",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", pg.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "customer_id", pg.UUID(as_uuid=True), sa.ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("reference_number", sa.Text, nullable=False),
        sa.Column("status", receipt_status, nullable=False, server_default="issued"),
        sa.Column("currency", sa.CHAR(3), nullable=False),
        sa.Column("amount_cents", sa.BigInteger, nullable=False),
        sa.Column("amount_in_words", sa.Text, nullable=False),
        sa.Column("balance_cents", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("payment_method", payment_method_type, nullable=False),
        sa.Column("payment_reference", sa.Text),
        sa.Column("paid_at", sa.Date, nullable=False),
        sa.Column("issued_by_user_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("issuer_printed_name", sa.Text, nullable=False),
        sa.Column("signature_image_url", sa.Text),
        sa.Column("corrects_receipt_id", pg.UUID(as_uuid=True), sa.ForeignKey("receipts.id")),
        sa.Column(
            "hosted_view_token",
            sa.Text,
            nullable=False,
            server_default=sa.text("encode(gen_random_bytes(16), 'hex')"),
        ),
        sa.Column("pdf_url", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "reference_number"),
    )
    op.create_index("idx_receipts_tenant_created", "receipts", ["tenant_id", sa.text("created_at DESC")])
    op.create_index("idx_receipts_customer", "receipts", ["customer_id"])
    op.create_index("idx_receipts_hosted_token", "receipts", ["hosted_view_token"], unique=True)

    op.create_table(
        "delivery_attempts",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("receipt_id", pg.UUID(as_uuid=True), sa.ForeignKey("receipts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("channel", delivery_channel, nullable=False),
        sa.Column("status", delivery_status, nullable=False, server_default="queued"),
        sa.Column("recipient", sa.Text, nullable=False),
        sa.Column("provider", sa.Text),
        sa.Column("provider_message_id", sa.Text),
        sa.Column("provider_response", pg.JSONB),
        sa.Column("attempt_number", sa.Integer, nullable=False, server_default="1"),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_delivery_receipt", "delivery_attempts", ["receipt_id"])
    op.create_index("idx_delivery_status", "delivery_attempts", ["status"])
    op.create_index("idx_delivery_provider_msg", "delivery_attempts", ["provider_message_id"])

    op.create_table(
        "api_keys",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", pg.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("key_prefix", sa.Text, nullable=False),
        sa.Column("key_hash", sa.Text, nullable=False),
        sa.Column("rate_limit_per_minute", sa.Integer, nullable=False, server_default="60"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_by_user_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("last_used_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_api_keys_tenant", "api_keys", ["tenant_id"])
    op.create_index("idx_api_keys_prefix", "api_keys", ["key_prefix"], unique=True)

    op.create_table(
        "suppressions",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", pg.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE")),
        sa.Column("channel", delivery_channel, nullable=False),
        sa.Column("contact", sa.Text, nullable=False),
        sa.Column("reason", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "channel", "contact"),
    )
    op.create_index("idx_suppressions_lookup", "suppressions", ["channel", "contact"])

    op.create_table(
        "audit_logs",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", pg.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_user_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("action", sa.Text, nullable=False),
        sa.Column("entity_type", sa.Text, nullable=False),
        sa.Column("entity_id", pg.UUID(as_uuid=True)),
        sa.Column("metadata", pg.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_audit_tenant_created", "audit_logs", ["tenant_id", sa.text("created_at DESC")])
    op.create_index("idx_audit_entity", "audit_logs", ["entity_type", "entity_id"])

    op.create_table(
        "usage_counters",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", pg.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period_start", sa.Date, nullable=False),
        sa.Column("period_end", sa.Date, nullable=False),
        sa.Column("emails_sent", sa.Integer, nullable=False, server_default="0"),
        sa.Column("sms_sent", sa.Integer, nullable=False, server_default="0"),
        sa.Column("receipts_created", sa.Integer, nullable=False, server_default="0"),
        sa.UniqueConstraint("tenant_id", "period_start", "period_end"),
    )
    op.create_index("idx_usage_tenant_period", "usage_counters", ["tenant_id", "period_start"])

    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        "CREATE TRIGGER trg_tenants_updated_at BEFORE UPDATE ON tenants "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at();"
    )
    op.execute(
        "CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON users "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at();"
    )
    op.execute(
        "CREATE TRIGGER trg_customers_updated_at BEFORE UPDATE ON customers "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at();"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_customers_updated_at ON customers")
    op.execute("DROP TRIGGER IF EXISTS trg_users_updated_at ON users")
    op.execute("DROP TRIGGER IF EXISTS trg_tenants_updated_at ON tenants")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at()")

    op.drop_table("usage_counters")
    op.drop_table("audit_logs")
    op.drop_table("suppressions")
    op.drop_table("api_keys")
    op.drop_table("delivery_attempts")
    op.drop_table("receipts")
    op.drop_table("customers")
    op.drop_table("users")
    op.drop_table("tenants")

    for enum_name in (
        "payment_method_type",
        "plan_tier",
        "delivery_status",
        "delivery_channel",
        "receipt_status",
        "user_role",
    ):
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
