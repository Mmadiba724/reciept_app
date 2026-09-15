import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.session import Base
from app.models.enums import DeliveryChannel, DeliveryStatus
from app.models.types import JSONBType, PortableEnum, UUIDType

delivery_channel_enum = PortableEnum(DeliveryChannel, name="delivery_channel")
delivery_status_enum = PortableEnum(DeliveryStatus, name="delivery_status")


class DeliveryAttempt(Base):
    __tablename__ = "delivery_attempts"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    receipt_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("receipts.id", ondelete="CASCADE"), nullable=False
    )
    channel: Mapped[DeliveryChannel] = mapped_column(delivery_channel_enum, nullable=False)
    status: Mapped[DeliveryStatus] = mapped_column(delivery_status_enum, nullable=False, default=DeliveryStatus.queued)
    recipient: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str | None] = mapped_column(Text)
    provider_message_id: Mapped[str | None] = mapped_column(Text)
    provider_response: Mapped[dict | None] = mapped_column(JSONBType())
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
