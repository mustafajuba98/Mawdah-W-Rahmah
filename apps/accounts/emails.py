from django.conf import settings
from django.utils import timezone
from django.utils.html import escape

from services.brevo_email import send_brevo_html

from .models import EmailVerificationPending
from .verification import generate_numeric_code, hash_verification_code, verification_expires_at


def build_verification_email_html(*, code: str, site_name: str) -> str:
    safe_code = escape(code)
    sn = escape(site_name)
    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="utf-8"></head>
<body style="font-family:Segoe UI,Tahoma,sans-serif;line-height:1.6;color:#1e2822;">
  <p>مرحباً،</p>
  <p>رمز تأكيد حسابك على <strong>{sn}</strong>:</p>
  <p style="font-size:1.75rem;font-weight:700;letter-spacing:0.2em;color:#2a5c47;">{safe_code}</p>
  <p>لا تشارك هذا الرمز مع أحد. صلاحيته محدودة.</p>
  <p style="color:#5a665e;font-size:0.9rem;">إذا لم تطلب هذا الحساب، تجاهل الرسالة.</p>
</body>
</html>"""


def issue_and_email_verification_code(user) -> None:
    """Store hashed code and send email via Brevo."""
    code = generate_numeric_code()
    expires = verification_expires_at()
    now = timezone.now()
    EmailVerificationPending.objects.update_or_create(
        user=user,
        defaults={
            "code_hash": hash_verification_code(code),
            "expires_at": expires,
            "last_sent_at": now,
        },
    )

    site_name = settings.SITE_NAME
    subject = f"{site_name} — رمز التحقق"
    send_brevo_html(
        to_email=user.email,
        subject=subject,
        html_body=build_verification_email_html(code=code, site_name=site_name),
        text_body=f"رمز التحقق: {code}",
    )
