from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.delivery import DeliveryAttempt
from app.models.enums import DeliveryChannel, DeliveryStatus
from app.models.suppression import Suppression

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

POSTMARK_STATUS_MAP = {
    "Delivery": DeliveryStatus.delivered,
    "Bounce": DeliveryStatus.bounced,
    "Open": DeliveryStatus.opened,
}

TWILIO_STATUS_MAP = {
    "queued": DeliveryStatus.queued,
    "sent": DeliveryStatus.sent,
    "delivered": DeliveryStatus.delivered,
    "failed": DeliveryStatus.failed,
    "undelivered": DeliveryStatus.failed,
}


@router.post("/postmark")
async def postmark_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.json()
    record_type = payload.get("RecordType")
    message_id = payload.get("MessageID")

    new_status = POSTMARK_STATUS_MAP.get(record_type)
    if message_id is None or new_status is None:
        return {"detail": "ignored"}

    result = await db.execute(
        select(DeliveryAttempt).where(DeliveryAttempt.provider_message_id == message_id)
    )
    attempt = result.scalar_one_or_none()
    if attempt is None:
        return {"detail": "no matching delivery attempt"}

    attempt.status = new_status
    attempt.resolved_at = datetime.now(timezone.utc)
    attempt.provider_response = payload

    if record_type == "Bounce" and payload.get("Type") in {"HardBounce", "SpamComplaint"}:
        db.add(
            Suppression(
                tenant_id=None,
                channel=DeliveryChannel.email,
                contact=attempt.recipient,
                reason="hard_bounce" if payload.get("Type") == "HardBounce" else "complaint",
            )
        )

    await db.commit()
    return {"detail": "ok"}


@router.post("/twilio")
async def twilio_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    form = await request.form()
    message_sid = form.get("MessageSid")
    message_status = form.get("MessageStatus")

    new_status = TWILIO_STATUS_MAP.get(message_status)
    if message_sid is None or new_status is None:
        return {"detail": "ignored"}

    result = await db.execute(
        select(DeliveryAttempt).where(DeliveryAttempt.provider_message_id == message_sid)
    )
    attempt = result.scalar_one_or_none()
    if attempt is None:
        return {"detail": "no matching delivery attempt"}

    attempt.status = new_status
    attempt.resolved_at = datetime.now(timezone.utc)
    attempt.provider_response = dict(form)

    if new_status == DeliveryStatus.failed and form.get("ErrorCode") in {"21610", "30007"}:
        db.add(
            Suppression(
                tenant_id=None,
                channel=DeliveryChannel.sms,
                contact=attempt.recipient,
                reason="stop_keyword" if form.get("ErrorCode") == "21610" else "carrier_filtered",
            )
        )

    await db.commit()
    return {"detail": "ok"}


@router.post("/twilio/sms-inbound")
async def twilio_inbound_sms(request: Request, db: AsyncSession = Depends(get_db)):
    """Handles inbound SMS, primarily for STOP keyword opt-out support (a
    carrier requirement, not optional)."""
    form = await request.form()
    body = (form.get("Body") or "").strip().upper()
    from_number = form.get("From")

    if body in {"STOP", "STOPALL", "UNSUBSCRIBE", "CANCEL", "END", "QUIT"} and from_number:
        existing = await db.execute(
            select(Suppression).where(Suppression.channel == DeliveryChannel.sms, Suppression.contact == from_number)
        )
        if existing.scalar_one_or_none() is None:
            db.add(
                Suppression(
                    tenant_id=None,
                    channel=DeliveryChannel.sms,
                    contact=from_number,
                    reason="stop_keyword",
                )
            )
            await db.commit()

    return {"detail": "ok"}
