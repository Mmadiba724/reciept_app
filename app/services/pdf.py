from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from app.core.config import get_settings

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)


def format_money(amount_cents: int, currency: str) -> str:
    major, minor = divmod(amount_cents, 100)
    return f"{currency} {major:,}.{minor:02d}"


def render_receipt_html(*, tenant, user, customer, receipt) -> str:
    template = _env.get_template("receipt.html")
    return template.render(
        tenant=tenant,
        user=user,
        customer=customer,
        receipt=receipt,
        amount_display=format_money(receipt.amount_cents, receipt.currency),
        balance_display="Nil" if receipt.balance_cents == 0 else format_money(receipt.balance_cents, receipt.currency),
    )


def render_receipt_pdf_bytes(*, tenant, user, customer, receipt) -> bytes:
    html_content = render_receipt_html(tenant=tenant, user=user, customer=customer, receipt=receipt)
    return HTML(string=html_content, base_url=str(TEMPLATES_DIR)).write_pdf()


def read_stored_pdf(*, tenant_id: str, receipt_id: str) -> bytes | None:
    settings = get_settings()
    file_path = Path(settings.storage_dir) / "pdfs" / tenant_id / f"{receipt_id}.pdf"
    if file_path.exists():
        return file_path.read_bytes()
    return None


def store_receipt_pdf(*, tenant_id: str, receipt_id: str, pdf_bytes: bytes) -> str:
    """Stores the PDF on local disk (MVP) and returns a public URL path.

    Swap this function's body for an S3/GCS upload later without changing
    callers — they only depend on getting back a URL.
    """
    settings = get_settings()
    pdf_dir = Path(settings.storage_dir) / "pdfs" / tenant_id
    pdf_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{receipt_id}.pdf"
    file_path = pdf_dir / filename
    file_path.write_bytes(pdf_bytes)

    return f"{settings.app_base_url}/static/pdfs/{tenant_id}/{filename}"
