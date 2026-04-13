"""Send transactional email via Brevo REST API (HTTPS — works on PythonAnywhere free tier)."""

from __future__ import annotations

import logging

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def send_brevo_html(*, to_email: str, subject: str, html_body: str, text_body: str = "") -> None:
    key = settings.BREVO_API_KEY
    sender_email = settings.BREVO_SENDER_EMAIL
    sender_name = settings.BREVO_SENDER_NAME
    if not key or not sender_email:
        raise ImproperlyConfigured(
            "Brevo is not configured: set DJANGO_BREVO_API_KEY and DJANGO_BREVO_SENDER_EMAIL in .env"
        )
    payload = {
        "sender": {"email": sender_email, "name": sender_name or sender_email},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_body,
    }
    if text_body:
        payload["textContent"] = text_body
    r = requests.post(
        BREVO_API_URL,
        json=payload,
        headers={
            "accept": "application/json",
            "content-type": "application/json",
            "api-key": key,
        },
        timeout=30,
    )
    if r.status_code >= 400:
        logger.warning("Brevo API error %s: %s", r.status_code, r.text[:500])
        r.raise_for_status()
