import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.types import UUIDType


class UsageCounter(Base):
    __tablename__ = "usage_counters"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    emails_sent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sms_sent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    receipts_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
