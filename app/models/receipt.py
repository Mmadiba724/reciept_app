import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.session import Base
from app.models.enums import PaymentMethodType, ReceiptStatus
from app.models.types import PortableEnum, UUIDType

receipt_status_enum = PortableEnum(ReceiptStatus, name="receipt_status")
payment_method_enum = PortableEnum(PaymentMethodType, name="payment_method_type")


class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False
    )
    reference_number: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ReceiptStatus] = mapped_column(receipt_status_enum, nullable=False, default=ReceiptStatus.issued)

    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    amount_in_words: Mapped[str] = mapped_column(Text, nullable=False)
    balance_cents: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    payment_method: Mapped[PaymentMethodType] = mapped_column(payment_method_enum, nullable=False)
    payment_reference: Mapped[str | None] = mapped_column(Text)
    paid_at: Mapped[date] = mapped_column(Date, nullable=False)

    issued_by_user_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), ForeignKey("users.id"), nullable=False)
    issuer_printed_name: Mapped[str] = mapped_column(Text, nullable=False)
    signature_image_url: Mapped[str | None] = mapped_column(Text)

    corrects_receipt_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType(), ForeignKey("receipts.id"), nullable=True
    )

    hosted_view_token: Mapped[str] = mapped_column(Text, nullable=False, default=lambda: uuid.uuid4().hex)
    pdf_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
