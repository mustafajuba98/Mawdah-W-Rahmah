from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class SignUpForm(UserCreationForm):
    applicant_gender = forms.ChoiceField(
        label="نوع مقدّم الطلب",
        choices=User.ApplicantGender.choices,
        required=True,
    )

    class Meta:
        model = User
        fields = ("email", "applicant_gender", "password1", "password2")

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        allowed = getattr(settings, "SIGNUP_ALLOWED_EMAIL_DOMAINS", None)
        if allowed:
            if "@" not in email:
                raise forms.ValidationError("صيغة البريد غير صحيحة.")
            domain = email.rsplit("@", 1)[-1].lower()
            if domain not in allowed:
                raise forms.ValidationError(
                    "يُقبل التسجيل من نطاقات بريد معروفة فقط (مثل Gmail وYahoo). "
                    "جرّب بريداً من أحد المزودين المسموحين."
                )
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = False
        user.email_verified_at = None
        if commit:
            user.save()
            if hasattr(self, "save_m2m"):
                self.save_m2m()
        return user


class EmailLoginForm(AuthenticationForm):
    username = forms.EmailField(label="البريد الإلكتروني")


class VerifyEmailForm(forms.Form):
    code = forms.RegexField(
        label="رمز التحقق (6 أرقام)",
        regex=r"^\d{6}$",
        max_length=6,
        min_length=6,
        widget=forms.TextInput(
            attrs={
                "class": "otp-input",
                "inputmode": "numeric",
                "pattern": r"\d{6}",
                "autocomplete": "one-time-code",
                "placeholder": "••••••",
                "maxlength": "6",
            }
        ),
    )
