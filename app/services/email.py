from __future__ import annotations

from typing import Any

from postmarker.core import PostmarkClient

from app.core.config import get_settings


def _client() -> PostmarkClient:
    settings = get_settings()
    return PostmarkClient(server_token=settings.postmark_server_token)


def send_verification_email(*, to_email: str, verify_url: str) -> dict[str, Any]:
    settings = get_settings()
    client = _client()
    return client.emails.send(
        From=settings.postmark_from_email,
        To=to_email,
        Subject="Verify your email",
        HtmlBody=f'<p>Welcome! Please verify your email by clicking <a href="{verify_url}">here</a>.</p>',
        TextBody=f"Welcome! Verify your email: {verify_url}",
        MessageStream="outbound",
    )


def send_password_reset_email(*, to_email: str, reset_url: str) -> dict[str, Any]:
    settings = get_settings()
    client = _client()
    return client.emails.send(
        From=settings.postmark_from_email,
        To=to_email,
        Subject="Reset your password",
        HtmlBody=f'<p>Click <a href="{reset_url}">here</a> to reset your password. If you did not request this, ignore this email.</p>',
        TextBody=f"Reset your password: {reset_url}",
        MessageStream="outbound",
    )


def send_receipt_email(
    *,
    to_email: str,
    business_name: str,
    amount_display: str,
    hosted_url: str,
    pdf_bytes: bytes | None,
    pdf_filename: str,
    mode: str = "attachment",
) -> dict[str, Any]:
    settings = get_settings()
    client = _client()

    html_body = (
        f"<p>Thank you for your payment of <strong>{amount_display}</strong> to "
        f"<strong>{business_name}</strong>.</p>"
        f'<p>You can view or download your receipt here: <a href="{hosted_url}">{hosted_url}</a></p>'
    )

    kwargs: dict[str, Any] = dict(
        From=settings.postmark_from_email,
        To=to_email,
        Subject=f"Your receipt from {business_name}",
        HtmlBody=html_body,
        TextBody=f"Thank you for your payment of {amount_display} to {business_name}. View your receipt: {hosted_url}",
        MessageStream="outbound",
    )

    if mode == "attachment" and pdf_bytes:
        import base64

        kwargs["Attachments"] = [
            {
                "Name": pdf_filename,
                "Content": base64.b64encode(pdf_bytes).decode("ascii"),
                "ContentType": "application/pdf",
            }
        ]

    return client.emails.send(**kwargs)
