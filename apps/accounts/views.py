from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, FormView

from .emails import issue_and_email_verification_code
from .forms import EmailLoginForm, SignUpForm, VerifyEmailForm
from .models import EmailVerificationPending, User
from .verification import code_matches_stored

PENDING_VERIFY_SESSION_KEY = "pending_email_verify_uid"


def mask_email(email: str) -> str:
    email = (email or "").strip()
    if "@" not in email:
        return "••••"
    local, _, domain = email.partition("@")
    if len(local) <= 2:
        masked = (local[:1] if local else "•") + "••••"
    else:
        masked = local[0] + "•" * min(4, len(local) - 2) + local[-1]
    return f"{masked}@{domain}"


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = "accounts/signup.html"
    success_url = reverse_lazy("verify_email")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        allowed = getattr(settings, "SIGNUP_ALLOWED_EMAIL_DOMAINS", None)
        ctx["signup_allowed_domains"] = allowed
        return ctx

    def form_valid(self, form):
        user = form.save(commit=False)
        user.profile_status = User.ProfileStatus.REGISTERED
        user.save()
        self.object = user
        try:
            issue_and_email_verification_code(user)
        except Exception:
            user.delete()
            messages.error(
                self.request,
                "تعذّر إرسال بريد التحقق. تحقّق من إعدادات Brevo في الخادم ثم أعد المحاولة.",
            )
            return self.form_invalid(form)
        self.request.session[PENDING_VERIFY_SESSION_KEY] = str(user.pk)
        messages.success(
            self.request,
            "أرسلنا رمز التحقق المكوّن من 6 أرقام إلى بريدك. أدخله في الخطوة التالية.",
        )
        return redirect("verify_email")


class VerifyEmailView(FormView):
    template_name = "accounts/verify_email.html"
    form_class = VerifyEmailForm

    def dispatch(self, request, *args, **kwargs):
        uid = request.session.get(PENDING_VERIFY_SESSION_KEY)
        if not uid:
            messages.info(
                request,
                "لا يوجد جلسة تحقق. إن كان عندك حساب غير مُفعّل، سجّل الدخول بنفس البريد وكلمة المرور "
                "للانتقال إلى صفحة الرمز، أو أنشئ حساباً جديداً.",
            )
            return redirect("login")
        if not User.objects.filter(pk=uid).exists():
            del request.session[PENDING_VERIFY_SESSION_KEY]
            messages.error(request, "انتهت الجلسة. سجّل من جديد.")
            return redirect("signup")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        uid = self.request.session.get(PENDING_VERIFY_SESSION_KEY)
        user = User.objects.filter(pk=uid).first()
        ctx["masked_email"] = mask_email(user.email) if user else ""
        ctx["resend_cooldown_seconds"] = settings.EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS
        pending = (
            getattr(user, "email_verification_pending", None) if user else None
        )
        ctx["can_resend_after_seconds"] = 0
        if pending:
            elapsed = (timezone.now() - pending.last_sent_at).total_seconds()
            cool = settings.EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS
            ctx["can_resend_after_seconds"] = max(0, int(cool - elapsed))
        return ctx

    def form_valid(self, form):
        uid = self.request.session.get(PENDING_VERIFY_SESSION_KEY)
        user = User.objects.filter(pk=uid).first()
        if not user:
            del self.request.session[PENDING_VERIFY_SESSION_KEY]
            messages.error(self.request, "انتهت الجلسة.")
            return redirect("signup")
        pending = getattr(user, "email_verification_pending", None)
        if not pending or pending.is_expired():
            messages.error(
                self.request,
                "انتهت صلاحية الرمز. استخدم «إعادة إرسال الرمز» ثم جرّب مرة أخرى.",
            )
            return redirect("verify_email")
        code = form.cleaned_data["code"]
        if not code_matches_stored(code, pending.code_hash):
            form.add_error("code", "الرمز غير صحيح.")
            return self.form_invalid(form)
        now = timezone.now()
        user.email_verified_at = now
        user.is_active = True
        user.save(update_fields=["email_verified_at", "is_active"])
        EmailVerificationPending.objects.filter(user=user).delete()
        del self.request.session[PENDING_VERIFY_SESSION_KEY]
        messages.success(self.request, "تم تأكيد بريدك. مرحباً بك.")
        login(self.request, user)
        return redirect("home")


class ResendVerificationView(View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        uid = request.session.get(PENDING_VERIFY_SESSION_KEY)
        if not uid:
            messages.info(request, "لا يوجد طلب تحقق.")
            return redirect("signup")
        user = User.objects.filter(pk=uid).first()
        if not user:
            del request.session[PENDING_VERIFY_SESSION_KEY]
            return redirect("signup")
        pending = getattr(user, "email_verification_pending", None)
        cool = settings.EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS
        if pending and not pending.is_expired():
            elapsed = (timezone.now() - pending.last_sent_at).total_seconds()
            if elapsed < cool:
                wait = int(cool - elapsed)
                messages.warning(
                    request,
                    f"يمكنك طلب رمز جديد بعد {wait} ثانية.",
                )
                return redirect("verify_email")
        try:
            issue_and_email_verification_code(user)
            messages.success(request, "أعدنا إرسال رمز التحقق إلى بريدك.")
        except Exception:
            messages.error(
                request,
                "تعذّر إرسال البريد. تحقّق من إعدادات Brevo أو حاول لاحقاً.",
            )
        return redirect("verify_email")


class EmailLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True
    authentication_form = EmailLoginForm

    def post(self, request, *args, **kwargs):
        """Inactive users fail Django auth; send them back to verify-email with optional new code."""
        email = (request.POST.get("username") or "").strip().lower()
        password = request.POST.get("password") or ""
        if email and password:
            user = User.objects.filter(email=email).first()
            if user and user.check_password(password):
                if user.profile_status == User.ProfileStatus.SUSPENDED:
                    messages.error(
                        request,
                        "تم إيقاف هذا الحساب. تواصل مع الإدارة إن كان ذلك خطأ.",
                    )
                    return redirect("login")
                if user.email_verified_at is None:
                    request.session[PENDING_VERIFY_SESSION_KEY] = str(user.pk)
                    pending = getattr(user, "email_verification_pending", None)
                    need_fresh_code = pending is None or pending.is_expired()
                    if need_fresh_code:
                        try:
                            issue_and_email_verification_code(user)
                            messages.success(
                                request,
                                "انتهت صلاحية الرمز السابق أو لم يعد هناك رمز فعّال. "
                                "أرسلنا رمزاً جديداً إلى بريدك — أدخله أدناه.",
                            )
                        except Exception:
                            messages.error(
                                request,
                                "تعذّر إرسال رمز جديد. تحقّق من إعدادات Brevo ثم أعد المحاولة.",
                            )
                            return redirect("login")
                    else:
                        messages.info(
                            request,
                            "أكمل تأكيد بريدك بإدخال الرمز المكوّن من 6 أرقام المرسل إلى بريدك.",
                        )
                    return redirect("verify_email")
        return super().post(request, *args, **kwargs)


class AppLogoutView(LogoutView):
    next_page = reverse_lazy("home")
